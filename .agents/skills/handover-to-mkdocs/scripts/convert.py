#!/usr/bin/env python3
"""인수인계 자료 원본 폴더(1. RAW)의 모든 파일을 마크다운 중간본으로 변환한다.

- kordoc: HWP·HWPX·HWPML·PDF·DOCX·XLS(X)·이미지
- OfficeCLI: PPTX (DOCX·XLSX는 kordoc 실패 시 대체 경로)
- 결과는 중간본 폴더에 평탄하게 저장하고, 파일별 상태를 manifest.json에 기록한다.
- 원본 해시가 같으면 다시 변환하지 않으므로 중단 후 재실행해도 이어서 진행된다.

표준 라이브러리만 사용한다(Windows·macOS 공통).
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import unicodedata
from datetime import datetime
from pathlib import Path

# 프로젝트 루트: .agents/skills/handover-to-mkdocs/scripts/convert.py 기준 네 단계 위
ROOT = Path(__file__).resolve().parents[4]
DEFAULT_SOURCE = ROOT / "1. RAW"
DEFAULT_OUT = ROOT / "2. 변환 중간본"
MANIFEST_NAME = "manifest.json"
REPORT_NAME = "변환 보고서.md"
MANIFEST_VERSION = 1

KORDOC_EXT = {
    ".hwp", ".hwpx", ".hwpml", ".hml", ".pdf",
    ".docx", ".docm", ".xlsx", ".xlsm", ".xls",
    ".png", ".jpg", ".jpeg", ".webp",
}
OFFICECLI_EXT = {".pptx"}
# kordoc이 실패하면 OfficeCLI로 다시 시도할 형식
OFFICECLI_FALLBACK_EXT = {".docx", ".xlsx"}
TEXT_EXT = {".txt", ".md"}
CSV_EXT = {".csv", ".tsv"}

# 변환하지 않고 보고서에 조치 방법만 남기는 형식
UNSUPPORTED_HINTS = {
    # 남겨 두면 매번 미지원으로 보고되므로 다시 저장한 파일로 바꿔 넣도록 안내한다
    ".doc": "Word에서 열어 .docx로 다시 저장하고, 원래 파일과 바꿔 넣으십시오.",
    ".ppt": "PowerPoint에서 열어 .pptx로 다시 저장하고, 원래 파일과 바꿔 넣으십시오.",
    ".pps": "PowerPoint에서 열어 .pptx로 다시 저장하고, 원래 파일과 바꿔 넣으십시오.",
    ".ppsx": "PowerPoint에서 열어 .pptx로 다시 저장하고, 원래 파일과 바꿔 넣으십시오.",
    ".rtf": "Word에서 열어 .docx로 다시 저장하고, 원래 파일과 바꿔 넣으십시오.",
    ".zip": "같은 위치에 압축을 풀고, 압축 파일은 원본 폴더에서 빼십시오.",
    ".7z": "같은 위치에 압축을 풀고, 압축 파일은 원본 폴더에서 빼십시오.",
    ".egg": "같은 위치에 압축을 풀고, 압축 파일은 원본 폴더에서 빼십시오.",
    ".alz": "같은 위치에 압축을 풀고, 압축 파일은 원본 폴더에서 빼십시오.",
    ".rar": "같은 위치에 압축을 풀고, 압축 파일은 원본 폴더에서 빼십시오.",
    # 한컴오피스·오픈오피스 형식
    ".cell": "한셀에서 열어 .xlsx로 다시 저장하고, 원래 파일과 바꿔 넣으십시오.",
    ".show": "한쇼에서 열어 .pptx로 다시 저장하고, 원래 파일과 바꿔 넣으십시오.",
    ".odt": "Word나 한글에서 열어 .docx로 다시 저장하고, 원래 파일과 바꿔 넣으십시오.",
    ".ods": "Excel이나 한셀에서 열어 .xlsx로 다시 저장하고, 원래 파일과 바꿔 넣으십시오.",
    ".odp": "PowerPoint나 한쇼에서 열어 .pptx로 다시 저장하고, 원래 파일과 바꿔 넣으십시오.",
    # 메일은 본문과 첨부 파일을 따로 꺼내야 한다
    ".msg": "Outlook에서 메일을 PDF로 인쇄해 넣고, 첨부 파일은 따로 저장해 원본 폴더에 넣으십시오.",
    ".eml": "메일 프로그램에서 열어 PDF로 인쇄해 넣고, 첨부 파일은 따로 저장해 원본 폴더에 넣으십시오.",
    # kordoc이 읽지 않는 이미지 형식
    ".gif": "그림판 등에서 열어 .png로 다시 저장하고, 원래 파일과 바꿔 넣으십시오.",
    ".bmp": "그림판 등에서 열어 .png로 다시 저장하고, 원래 파일과 바꿔 넣으십시오.",
    ".tif": "그림판 등에서 열어 .png로 다시 저장하고, 원래 파일과 바꿔 넣으십시오.",
    ".tiff": "그림판 등에서 열어 .png로 다시 저장하고, 원래 파일과 바꿔 넣으십시오.",
}

# 목록에서 아예 제외하는 시스템·임시 파일
IGNORED_NAMES = {"thumbs.db", "desktop.ini", ".ds_store"}

FAIL_HINTS = {
    "ENCRYPTED": "암호가 걸린 문서입니다. 암호를 풀어 다시 저장하고, 원래 파일과 바꿔 넣으십시오.",
    "DRM_PROTECTED": "문서보안(DRM)이 걸려 있어 열 수 없습니다. 보안을 해제한 사본이 필요합니다.",
    "CORRUPTED": "파일이 손상되었습니다. 원본을 다시 받아야 합니다.",
    "EMPTY_INPUT": "빈 파일입니다.",
    "IMAGE_BASED_PDF": "스캔 PDF입니다. OCR로도 글자를 읽지 못했습니다.",
    "UNSUPPORTED_FORMAT": "확장자와 실제 형식이 다를 수 있습니다. 원본 프로그램에서 열어 확인하십시오.",
    "MISSING_DEPENDENCY": "kordoc 선택 의존성이 없습니다. README의 kordoc 설치 절을 확인하십시오.",
    "TIMEOUT": "변환 시간이 제한을 넘었습니다. 파일을 나누거나 --timeout을 늘리십시오.",
    # 아래는 이 스크립트가 붙이는 코드다
    "TOOL_MISSING": "변환 도구가 없습니다. convert.py --check로 확인하고 설치 스크립트를 실행하십시오.",
    "PARSE_ERROR": "kordoc이 파일을 읽지 못했습니다. 원본 프로그램에서 열어 다시 저장해 보십시오.",
    "OFFICECLI_ERROR": "OfficeCLI가 파일을 읽지 못했습니다. 원본 프로그램에서 열어 다시 저장해 보십시오.",
}

CSV_MAX_ROWS = 500
WINDOWS = os.name == "nt"


# ---------------------------------------------------------------------------
# 공통 유틸리티
# ---------------------------------------------------------------------------

def nfc(text: str) -> str:
    # macOS에서 온 파일명은 NFD일 수 있으므로 기록용 문자열은 NFC로 통일한다
    return unicodedata.normalize("NFC", text)


def file_id(rel_posix: str) -> str:
    return hashlib.sha1(nfc(rel_posix).encode("utf-8")).hexdigest()[:8]


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def safe_name(name: str, limit: int = 60) -> str:
    # Windows에서 쓸 수 없는 문자를 바꾸고 길이를 제한한다
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", nfc(name)).strip(" .")
    return name[:limit] or "untitled"


def read_text_any(path: Path) -> str:
    raw = path.read_bytes()
    for enc in ("utf-8-sig", "cp949", "euc-kr"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def md_escape_cell(value: str) -> str:
    return value.replace("|", "\\|").replace("\r", "").replace("\n", "<br>").strip()


def md_table(rows: list[list[str]], max_rows: int | None = None) -> str:
    if not rows:
        return ""
    width = max(len(r) for r in rows)
    rows = [r + [""] * (width - len(r)) for r in rows]
    total = len(rows) - 1
    body = rows[1:] if max_rows is None else rows[1:max_rows + 1]
    lines = ["| " + " | ".join(md_escape_cell(c) for c in rows[0]) + " |",
             "| " + " | ".join("---" for _ in range(width)) + " |"]
    lines += ["| " + " | ".join(md_escape_cell(c) for c in r) + " |" for r in body]
    if max_rows is not None and total > max_rows:
        lines.append(f"\n> 전체 {total}행 가운데 앞 {max_rows}행만 옮겼습니다. 나머지는 원본을 확인하십시오.")
    return "\n".join(lines)


def decode_output(raw: bytes) -> str:
    # .NET 프로그램(OfficeCLI)은 한국어 Windows에서 CP949로 출력할 수 있으므로 UTF-8 실패 시 CP949로 읽는다
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return raw.decode("cp949", errors="replace")


def run(cmd: list[str], timeout: int, env: dict | None = None) -> subprocess.CompletedProcess:
    res = subprocess.run(cmd, capture_output=True, timeout=timeout, env=env)
    res.stdout, res.stderr = decode_output(res.stdout), decode_output(res.stderr)
    return res


def write_json_atomic(path: Path, data) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, path)


# ---------------------------------------------------------------------------
# 도구 탐색
# ---------------------------------------------------------------------------

def refresh_path() -> None:
    """설치 스크립트가 방금 설치한 도구를 찾을 수 있도록 PATH를 보강한다.

    이미 실행 중인 에이전트는 설치 전의 PATH를 물려받으므로, 새로 설치한 node·kordoc·officecli를 찾지 못한다.
    Windows는 레지스트리의 PATH를 다시 읽고, 두 운영체제 모두 알려진 설치 폴더를 뒤에 덧붙인다.
    """
    dirs: list[str] = []
    home = Path.home()
    if WINDOWS:
        try:
            import winreg
            for root, key in ((winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment"),
                              (winreg.HKEY_CURRENT_USER, "Environment")):
                try:
                    with winreg.OpenKey(root, key) as k:
                        dirs += os.path.expandvars(winreg.QueryValueEx(k, "Path")[0]).split(os.pathsep)
                except OSError:
                    pass
        except ImportError:
            pass
        env = os.environ
        dirs += [
            str(Path(env.get("ProgramFiles", r"C:\Program Files")) / "nodejs"),
            str(Path(env.get("APPDATA", home / "AppData/Roaming")) / "npm"),
            str(Path(env.get("LOCALAPPDATA", home / "AppData/Local")) / "OfficeCLI"),
        ]
    else:
        dirs += ["/opt/homebrew/bin", "/usr/local/bin", str(home / ".local/bin")]
    current = os.environ.get("PATH", "").split(os.pathsep)
    seen = {os.path.normcase(d) for d in current if d}
    extra = []
    for d in dirs:
        d = d.strip()
        if d and os.path.normcase(d) not in seen and Path(d).is_dir():
            extra.append(d)
            seen.add(os.path.normcase(d))
    if extra:
        os.environ["PATH"] = os.pathsep.join(current + extra)


def find_kordoc() -> list[str] | None:
    """kordoc 실행 명령을 찾는다. Windows의 .cmd 래퍼를 피하려고 node로 cli.js를 직접 실행한다."""
    node = shutil.which("node")
    env_cli = os.environ.get("KORDOC_CLI")
    if node and env_cli and Path(env_cli).is_file():
        return [node, env_cli]
    if node and shutil.which("npm"):
        try:
            # npm은 Windows에서 npm.cmd이므로 인자 없는 고정 명령에 한해 shell을 쓴다
            res = subprocess.run("npm root -g", shell=True, capture_output=True, text=True,
                                 encoding="utf-8", errors="replace", timeout=60)
            pkg_dir = Path(res.stdout.strip()) / "kordoc"
            pkg = json.loads((pkg_dir / "package.json").read_text(encoding="utf-8"))
            bin_rel = pkg["bin"]["kordoc"] if isinstance(pkg.get("bin"), dict) else pkg["bin"]
            cli = pkg_dir / bin_rel
            if cli.is_file():
                return [node, str(cli)]
        except (OSError, ValueError, KeyError, subprocess.TimeoutExpired):
            pass
    if not WINDOWS and shutil.which("kordoc"):
        return [shutil.which("kordoc")]
    npx = shutil.which("npx")
    if npx:
        return [npx, "-y", "kordoc"]
    return None


def find_officecli() -> list[str] | None:
    exe = shutil.which("officecli")
    return [exe] if exe else None


def tool_versions(kordoc: list[str] | None, officecli: list[str] | None) -> dict:
    info = {"node": None, "kordoc": None, "officecli": None}
    node = shutil.which("node")
    if node:
        info["node"] = run([node, "--version"], 30).stdout.strip()
    if kordoc:
        try:
            info["kordoc"] = run(kordoc + ["--version"], 180).stdout.strip() or "설치됨"
        except (OSError, subprocess.TimeoutExpired):
            pass
    if officecli:
        try:
            info["officecli"] = run(officecli + ["--version"], 60, officecli_env()).stdout.strip()
        except (OSError, subprocess.TimeoutExpired):
            pass
    return info


VENV_PYTHON = ROOT / (".venv/Scripts/python.exe" if os.name == "nt" else ".venv/bin/python")
# 사이트 빌드에 필요한 패키지. mkdocs-material이 pymdown-extensions 등 확장도 함께 설치한다
SITE_PACKAGES = ("mkdocs", "mkdocs-material")


def site_versions() -> dict:
    """프로젝트 가상환경(.venv)의 Python·MkDocs·Material for MkDocs 버전을 확인한다.

    이 스크립트는 시스템 파이썬으로 실행될 수도 있으므로 .venv의 파이썬을 따로 호출한다.
    """
    info = {"python": None, **{name: None for name in SITE_PACKAGES}}
    if not VENV_PYTHON.exists():
        return info
    code = (
        "import platform, importlib.metadata as m\n"
        "print(platform.python_version())\n"
        f"for n in {SITE_PACKAGES!r}:\n"
        "    try: print(m.version(n))\n"
        "    except m.PackageNotFoundError: print('')\n"
    )
    try:
        lines = run([str(VENV_PYTHON), "-c", code], 60).stdout.splitlines()
    except (OSError, subprocess.TimeoutExpired):
        return info
    for key, val in zip(info, lines):
        info[key] = val.strip() or None
    return info


def officecli_env() -> dict:
    env = dict(os.environ)
    env["OFFICECLI_SKIP_UPDATE"] = "1"
    return env


# ---------------------------------------------------------------------------
# 변환기
# ---------------------------------------------------------------------------

def parse_fail_json(stdout: str) -> dict | None:
    start = stdout.find("{")
    if start < 0:
        return None
    try:
        data = json.loads(stdout[start:])
    except ValueError:
        return None
    return data if isinstance(data, dict) and data.get("success") is False else None


def convert_kordoc(kordoc: list[str], src: Path, out_md: Path, timeout: int, ocr: bool) -> tuple[bool, str, str]:
    """(성공 여부, 오류 코드, 오류 문구)를 돌려준다."""
    cmd = kordoc + [str(src), "-o", str(out_md)]
    if ocr:
        cmd.append("--ocr")
    try:
        res = run(cmd, timeout)
    except subprocess.TimeoutExpired:
        return False, "TIMEOUT", f"{timeout}초 초과"
    if res.returncode == 0 and out_md.is_file():
        return True, "", ""
    fail = parse_fail_json(res.stdout) or {}
    return False, fail.get("code", "PARSE_ERROR"), fail.get("error", (res.stderr or res.stdout).strip()[-300:])


def strip_path_prefix(line: str) -> str:
    # "[/body/p[@paraId=..]] 본문" 처럼 중첩 대괄호로 된 경로 접두어를 떼어 낸다
    if not line.startswith("[/"):
        return line
    depth = 0
    for i, ch in enumerate(line):
        if ch == "[":
            depth += 1
        elif ch == "]":
            depth -= 1
            if depth == 0:
                return line[i + 1:].lstrip()
    return line


def officecli_text(officecli: list[str], src: Path, timeout: int) -> tuple[bool, str, str]:
    try:
        res = run(officecli + ["view", str(src), "text"], timeout, officecli_env())
    except subprocess.TimeoutExpired:
        return False, "", f"{timeout}초 초과"
    if res.returncode != 0:
        return False, "", (res.stderr or res.stdout).strip()[-300:]
    return True, res.stdout, ""


def pptx_to_md(text: str) -> str:
    out = []
    for line in text.splitlines():
        m = re.match(r"^=== /slide\[(\d+)\] ===$", line.strip())
        if m:
            out.append(f"\n## 슬라이드 {m.group(1)}\n")
        elif line.strip():
            out.append(strip_path_prefix(line))
    return "\n".join(out).strip() + "\n"


def docx_to_md(text: str) -> str:
    return "\n\n".join(strip_path_prefix(l) for l in text.splitlines() if l.strip()) + "\n"


def col_index(letters: str) -> int:
    n = 0
    for ch in letters:
        n = n * 26 + (ord(ch) - 64)
    return n - 1


def xlsx_to_md(text: str) -> str:
    sheets: list[tuple[str, dict[int, dict[int, str]]]] = []
    for line in text.splitlines():
        m = re.match(r"^=== Sheet: (.*) ===$", line.strip())
        if m:
            sheets.append((m.group(1), {}))
            continue
        if not sheets or not line.strip():
            continue
        for cell in strip_path_prefix(line).split("\t"):
            cm = re.match(r"^([A-Z]+)(\d+)=(.*)$", cell)
            if cm:
                sheets[-1][1].setdefault(int(cm.group(2)), {})[col_index(cm.group(1))] = cm.group(3)
    parts = []
    for name, grid in sheets:
        parts.append(f"## {name}\n")
        if not grid:
            parts.append("(빈 시트)\n")
            continue
        width = max(max(r) for r in grid.values()) + 1
        rows = [[grid[r].get(c, "") for c in range(width)] for r in sorted(grid)]
        parts.append(md_table(rows, CSV_MAX_ROWS) + "\n")
    return "\n".join(parts)


def convert_officecli(officecli: list[str], src: Path, out_md: Path, timeout: int) -> tuple[bool, str, str]:
    ok, text, err = officecli_text(officecli, src, timeout)
    if not ok:
        return False, "OFFICECLI_ERROR", err
    ext = src.suffix.lower()
    md = pptx_to_md(text) if ext == ".pptx" else xlsx_to_md(text) if ext == ".xlsx" else docx_to_md(text)
    out_md.write_text(md, encoding="utf-8")
    return True, "", ""


def convert_text(src: Path, out_md: Path) -> tuple[bool, str, str]:
    text = read_text_any(src)
    if src.suffix.lower() in CSV_EXT:
        delim = "\t" if src.suffix.lower() == ".tsv" else ","
        rows = list(csv.reader(io.StringIO(text), delimiter=delim))
        text = md_table(rows, CSV_MAX_ROWS) + "\n"
    out_md.write_text(text, encoding="utf-8")
    return True, "", ""


# ---------------------------------------------------------------------------
# 목록 작성과 실행
# ---------------------------------------------------------------------------

def is_ignored(path: Path) -> bool:
    name = path.name
    return name.startswith(".") or name.startswith("~$") or name.lower() in IGNORED_NAMES


def classify(ext: str) -> str:
    if ext in KORDOC_EXT:
        return "kordoc"
    if ext in OFFICECLI_EXT:
        return "officecli"
    if ext in TEXT_EXT or ext in CSV_EXT:
        return "text"
    return "unsupported"


def scan(source: Path) -> list[Path]:
    files = []
    for dirpath, dirnames, filenames in os.walk(source):
        dirnames[:] = sorted(d for d in dirnames if not d.startswith("."))
        for fn in sorted(filenames):
            p = Path(dirpath) / fn
            if not is_ignored(p):
                files.append(p)
    return files


def load_manifest(out: Path) -> dict:
    path = out / MANIFEST_NAME
    if path.is_file():
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict) and "files" in data:
            return data
    return {"version": MANIFEST_VERSION, "files": {}}


def images_dir_for(out: Path, out_md: Path) -> str | None:
    d = out / "images" / out_md.stem
    return d.relative_to(out).as_posix() if d.is_dir() else None


def remove_outputs(out: Path, output: str) -> None:
    # 원본이 사라졌거나 다시 변환할 때, 이전 중간본이 최신 내용처럼 검색되지 않도록 지운다
    out_md = out / output
    out_md.unlink(missing_ok=True)
    shutil.rmtree(out / "images" / out_md.stem, ignore_errors=True)


def convert_one(entry: dict, src: Path, out: Path, tools: dict, args) -> None:
    ext = entry["ext"]
    out_md = out / entry["output"]
    route = classify(ext)
    entry.update({"tool": None, "status": None, "error_code": None, "error": None, "hint": None})
    remove_outputs(out, entry["output"])

    if route == "unsupported":
        entry.update(status="unsupported", hint=UNSUPPORTED_HINTS.get(ext, "변환할 수 있는 형식이 아닙니다. 필요하면 내용을 직접 확인하십시오."))
        return

    attempts = []
    if route == "kordoc":
        attempts.append("kordoc")
        if ext in OFFICECLI_FALLBACK_EXT:
            attempts.append("officecli")
    elif route == "officecli":
        attempts.append("officecli")
    else:
        attempts.append("text")

    code, err = "", ""
    for tool in attempts:
        if tool == "kordoc":
            if not tools["kordoc"]:
                code, err = "TOOL_MISSING", "kordoc을 찾을 수 없습니다."
                continue
            ok, code, err = convert_kordoc(tools["kordoc"], src, out_md, args.timeout, args.ocr)
            if not ok and code == "IMAGE_BASED_PDF" and not args.ocr:
                # 스캔 PDF는 OCR을 켜고 한 번 더 시도한다(첫 실행 시 모델을 내려받음)
                ok, code, err = convert_kordoc(tools["kordoc"], src, out_md, args.timeout, True)
                entry["ocr"] = True
        elif tool == "officecli":
            if not tools["officecli"]:
                code, err = "TOOL_MISSING", "OfficeCLI를 찾을 수 없습니다."
                continue
            ok, code, err = convert_officecli(tools["officecli"], src, out_md, args.timeout)
        else:
            ok, code, err = convert_text(src, out_md)
        if ok:
            size = out_md.stat().st_size
            entry.update(tool=tool, status="converted" if size > 0 else "empty",
                         chars=len(out_md.read_text(encoding="utf-8", errors="replace")),
                         images=images_dir_for(out, out_md))
            if size == 0:
                entry["hint"] = "변환 결과가 비어 있습니다. 원본을 직접 확인하십시오."
            return
    entry.update(status="failed", error_code=code, error=err,
                 hint=FAIL_HINTS.get(code, "원본 프로그램에서 열리는지 확인하고, 다시 저장한 파일로 바꿔 넣으십시오."))


def write_report(out: Path, manifest: dict, source: Path) -> dict:
    files = manifest["files"]
    by_status: dict[str, int] = {}
    by_ext: dict[str, int] = {}
    for e in files.values():
        by_status[e["status"]] = by_status.get(e["status"], 0) + 1
        by_ext[e["ext"] or "(없음)"] = by_ext.get(e["ext"] or "(없음)", 0) + 1

    def rows(pred, cols):
        sel = [e for e in files.values() if pred(e)]
        if not sel:
            return "없음\n"
        head = "| " + " | ".join(c[0] for c in cols) + " |\n| " + " | ".join("---" for _ in cols) + " |\n"
        return head + "\n".join("| " + " | ".join(md_escape_cell(str(c[1](e) or "")) for c in cols) + " |" for e in sel) + "\n"

    labels = {"converted": "변환 완료", "empty": "빈 결과", "failed": "실패",
              "unsupported": "미지원 형식", "removed": "원본 삭제됨"}
    lines = [
        "# 변환 보고서", "",
        f"- **실행 시각**: {manifest['updated_at']}",
        f"- **원본 폴더**: `{nfc(source.name)}`",
        f"- **전체 파일**: {len(files)}개", "",
        "## 상태별 현황", "",
        "| 상태 | 개수 |", "| --- | ---: |",
        *[f"| {labels.get(k, k)} | {v} |" for k, v in sorted(by_status.items())], "",
        "## 형식별 현황", "",
        "| 확장자 | 개수 |", "| --- | ---: |",
        *[f"| {k} | {v} |" for k, v in sorted(by_ext.items())], "",
        "## 조치가 필요한 파일", "",
        rows(lambda e: e["status"] in ("failed", "unsupported", "empty"),
             [("원본 경로", lambda e: e["source"]), ("상태", lambda e: labels.get(e["status"], e["status"])),
              ("오류 코드", lambda e: e.get("error_code")), ("조치 방법", lambda e: e.get("hint"))]),
        "## 다시 반영해야 하는 문서", "",
        "원본이 바뀌었거나 삭제되어 MkDocs 문서를 고쳐야 합니다.", "",
        rows(lambda e: e.get("needs_republish"),
             [("원본 경로", lambda e: e["source"]), ("상태", lambda e: labels.get(e["status"], e["status"])),
              ("반영된 문서", lambda e: ", ".join(e.get("published") or []))]),
    ]
    (out / REPORT_NAME).write_text("\n".join(lines), encoding="utf-8")
    return by_status


def cmd_check(tools: dict) -> int:
    info = {**site_versions(), **tool_versions(tools["kordoc"], tools["officecli"])}
    ok = True
    for name, link in (("python", "프로젝트 가상환경(.venv)"),
                       ("mkdocs", "https://www.mkdocs.org/"),
                       ("mkdocs-material", "https://squidfunk.github.io/mkdocs-material/"),
                       ("node", "https://nodejs.org/"),
                       ("kordoc", "https://github.com/chrisryugj/kordoc"),
                       ("officecli", "https://github.com/iOfficeAI/OfficeCLI")):
        ver = info[name]
        print(f"{name:16s} {ver or '없음'}" + ("" if ver else f"  → 설치 안내: {link}"))
        ok = ok and bool(ver)
    if not ok:
        script = r"setup\setup-windows.cmd" if WINDOWS else "bash setup/setup-mac.sh"
        print(f"\n설치되지 않은 도구가 있습니다. 프로젝트 폴더에서 {script}를 실행하거나 README.md의 설치 안내를 따르십시오.")
    if tools["kordoc"] and tools["kordoc"][-1] == "kordoc" and "-y" in tools["kordoc"]:
        print("참고: kordoc을 npx로 실행합니다. 파일이 많으면 'npm install -g kordoc --allow-scripts=onnxruntime-node,protobufjs'로 설치하는 편이 빠릅니다.")
    return 0 if ok else 1


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description="인수인계 자료 원본을 마크다운 중간본으로 변환합니다.")
    ap.add_argument("--source", type=Path, default=DEFAULT_SOURCE, help="원본 폴더")
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT, help="중간본 폴더")
    ap.add_argument("--check", action="store_true", help="필요한 도구의 설치 여부만 확인")
    ap.add_argument("--dry-run", action="store_true", help="변환하지 않고 대상 목록과 처리 경로만 출력")
    ap.add_argument("--force", action="store_true", help="이미 변환한 파일도 다시 변환")
    ap.add_argument("--ocr", action="store_true", help="모든 PDF·이미지에 OCR 사용")
    ap.add_argument("--timeout", type=int, default=600, help="파일 하나의 변환 제한 시간(초)")
    args = ap.parse_args()

    refresh_path()
    tools = {"kordoc": find_kordoc(), "officecli": find_officecli()}
    if args.check:
        return cmd_check(tools)

    source, out = args.source.resolve(), args.out.resolve()
    if not source.is_dir():
        print(f"원본 폴더가 없습니다: {source}")
        return 1
    files = scan(source)
    if args.dry_run:
        for p in files:
            rel = nfc(p.relative_to(source).as_posix())
            print(f"{classify(p.suffix.lower()):12s} {rel}")
        print(f"\n대상 파일 {len(files)}개")
        return 0

    out.mkdir(parents=True, exist_ok=True)
    manifest = load_manifest(out)
    entries: dict = manifest["files"]
    seen = set()
    total = len(files)
    for i, src in enumerate(files, 1):
        rel = nfc(src.relative_to(source).as_posix())
        fid = file_id(rel)
        seen.add(fid)
        digest = sha256_of(src)
        prev = entries.get(fid, {})
        output = f"{fid}_{safe_name(src.stem)}{src.suffix.lower()}.md"
        unchanged = (prev.get("sha256") == digest and prev.get("status") in ("converted", "empty", "unsupported")
                     and (prev.get("status") == "unsupported" or (out / output).is_file()))
        if unchanged and not args.force:
            print(f"[{i}/{total}] 건너뜀(변경 없음) {rel}")
            continue
        entry = {
            "id": fid, "source": rel, "ext": src.suffix.lower(), "size": src.stat().st_size,
            "sha256": digest, "output": output,
            "modified": datetime.fromtimestamp(src.stat().st_mtime).strftime("%Y-%m-%d"),
            # 2단계(MkDocs 반영) 기록은 재변환해도 보존한다
            "published": prev.get("published", []),
            # 재반영 표시는 에이전트가 문서를 고친 뒤 직접 끈다
            "needs_republish": prev.get("needs_republish", False)
            or (bool(prev.get("published")) and prev.get("sha256") != digest),
        }
        convert_one(entry, src, out, tools, args)
        entries[fid] = entry
        mark = {"converted": "완료", "empty": "빈 결과", "failed": "실패", "unsupported": "미지원"}[entry["status"]]
        print(f"[{i}/{total}] {mark:4s} {rel}" + (f"  ({entry['error_code']})" if entry.get("error_code") else ""))
        manifest["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")
        write_json_atomic(out / MANIFEST_NAME, manifest)

    # 원본 폴더에서 사라진 파일은 삭제 표시와 함께 중간본을 지우고, 반영된 문서가 있으면 재반영 대상으로 둔다
    for fid, e in entries.items():
        if fid not in seen and e.get("status") != "removed":
            e["status"] = "removed"
            e["needs_republish"] = bool(e.get("published"))
            if e.get("output"):
                remove_outputs(out, e["output"])
    manifest["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")
    manifest["tools"] = tool_versions(tools["kordoc"], tools["officecli"])
    write_json_atomic(out / MANIFEST_NAME, manifest)
    by_status = write_report(out, manifest, source)

    print("\n요약: " + ", ".join(f"{k} {v}" for k, v in sorted(by_status.items())))
    print(f"보고서: {out / REPORT_NAME}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
