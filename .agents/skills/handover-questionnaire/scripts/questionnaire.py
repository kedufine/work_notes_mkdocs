#!/usr/bin/env python3
"""업무인수인계 질문지(엑셀)를 만들고, 인계자가 회신한 질문지에서 답변을 읽는다.

- build: 질문 목록(JSON)을 읽어 '3. 업무인수인계 질문지' 폴더에 .xlsx 질문지를 만든다.
- read : 회신받은 .xlsx에서 질문과 답변을 읽어 JSON으로 출력한다.
- list : 질문지 폴더의 파일별 질문 수와 답변 수를 보여 준다.

표준 라이브러리만 사용한다(Windows·macOS 공통).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
import zipfile
from datetime import date, datetime
from pathlib import Path
from xml.etree import ElementTree as ET
from xml.sax.saxutils import escape

# 프로젝트 루트: .agents/skills/handover-questionnaire/scripts/questionnaire.py 기준 네 단계 위
ROOT = Path(__file__).resolve().parents[4]
DEFAULT_DIR = ROOT / "3. 업무인수인계 질문지"
FILE_SUFFIX = "업무인계인수 질문지"
GUIDE_SHEET = "안내"
QUESTION_SHEET = "질문지"
PRIORITIES = ("상", "중", "하")

# (스펙 키, 열 제목, 열 너비, 셀 스타일 번호)
COLUMNS = [
    ("id", "번호", 9, 4),
    ("category", "업무 분야", 16, 4),
    ("source", "관련 자료", 30, 3),
    ("context", "관련 내용", 34, 3),
    ("question", "질문", 54, 3),
    ("type", "질문 유형", 13, 4),
    ("priority", "중요도", 8, 4),
    ("answer", "답변 (인계자 작성)", 60, 5),
    ("note", "참고 자료·비고 (인계자 작성)", 30, 5),
    ("doc", "반영 문서 (관리용, 작성 불필요)", 36, 6),
]
# 회신 파일의 열 제목(괄호 설명 제외) → 스펙 키
HEADER_KEYS = {re.sub(r"\(.*?\)", "", title).strip(): key for key, title, _, _ in COLUMNS}
# 인계자가 채우는 열
ANSWER_KEYS = ("answer", "note")

GUIDE_LINES = [
    "'질문지' 시트의 노란색 칸(답변, 참고 자료·비고)만 작성해 주시면 됩니다.",
    "중요도 '상'은 업무를 시작하는 데 꼭 필요한 항목입니다. 시간이 부족하면 '상'부터 작성해 주십시오.",
    "답변은 기억나는 범위에서 자유롭게 적어 주십시오. 모르거나 해당 사항이 없으면 '모름', '해당 없음'이라고 적어 주십시오.",
    "관련 파일이나 화면 캡처가 있으면 '참고 자료·비고' 칸에 파일명을 적고 이 파일과 함께 보내 주십시오.",
    "질문 외에 전달할 내용이 있으면 표 맨 아래에 행을 추가하여 '질문'과 '답변' 칸에 적어 주십시오.",
    "번호와 '반영 문서' 칸은 답변을 문서에 반영할 때 사용하는 관리용 값이므로 수정하지 말아 주십시오.",
]

NS_MAIN = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
NS_REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
NS_PKG_REL = "http://schemas.openxmlformats.org/package/2006/relationships"
XML_HEAD = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
ILLEGAL_XML = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")


# ---------------------------------------------------------------------------
# 공통 유틸
# ---------------------------------------------------------------------------

def nfc(text: str) -> str:
    return unicodedata.normalize("NFC", text)


def clean(value) -> str:
    """셀에 넣을 문자열로 정리한다. XML에 쓸 수 없는 제어 문자는 지운다."""
    if value is None:
        return ""
    text = str(value).replace("\r\n", "\n").replace("\r", "\n")
    return ILLEGAL_XML.sub("", nfc(text)).strip()


def col_letter(index: int) -> str:
    letters = ""
    index += 1
    while index:
        index, rem = divmod(index - 1, 26)
        letters = chr(65 + rem) + letters
    return letters


def col_index(ref: str) -> int:
    n = 0
    for ch in ref:
        if not ch.isalpha():
            break
        n = n * 26 + (ord(ch.upper()) - 64)
    return n - 1


def parse_date(text: str | None) -> date:
    if not text:
        return date.today()
    return datetime.strptime(text.strip(), "%Y-%m-%d").date()


# ---------------------------------------------------------------------------
# 엑셀 쓰기
# ---------------------------------------------------------------------------

class SharedStrings:
    def __init__(self) -> None:
        self.index: dict[str, int] = {}

    def add(self, text: str) -> int:
        return self.index.setdefault(text, len(self.index))

    def xml(self) -> str:
        items = "".join(f'<si><t xml:space="preserve">{escape(t)}</t></si>' for t in self.index)
        n = len(self.index)
        return f'{XML_HEAD}<sst xmlns="{NS_MAIN}" count="{n}" uniqueCount="{n}">{items}</sst>'


def cell(sst: SharedStrings, col: int, row: int, text: str, style: int) -> str:
    ref = f"{col_letter(col)}{row}"
    if text == "":
        return f'<c r="{ref}" s="{style}"/>'
    return f'<c r="{ref}" s="{style}" t="s"><v>{sst.add(text)}</v></c>'


def styles_xml() -> str:
    def font(extra: str = "", size: int = 10, color: str = "") -> str:
        col = f'<color rgb="{color}"/>' if color else ""
        return f'<font>{extra}<sz val="{size}"/>{col}<name val="맑은 고딕"/><family val="2"/><charset val="129"/></font>'

    def fill(rgb: str) -> str:
        return f'<fill><patternFill patternType="solid"><fgColor rgb="{rgb}"/><bgColor indexed="64"/></patternFill></fill>'

    def xf(font_id: int, fill_id: int, border_id: int, horizontal: str = "", num_fmt: int = 0) -> str:
        h = f' horizontal="{horizontal}"' if horizontal else ""
        return (f'<xf numFmtId="{num_fmt}" fontId="{font_id}" fillId="{fill_id}" borderId="{border_id}" xfId="0" '
                f'applyNumberFormat="1" applyFont="1" applyFill="1" applyBorder="1" applyAlignment="1">'
                f'<alignment{h} vertical="top" wrapText="1"/></xf>')

    side = '<{0} style="thin"><color rgb="FFBFBFBF"/></{0}>'
    border = "".join(side.format(s) for s in ("left", "right", "top", "bottom"))
    fonts = [font(), font("<b/>", color="FFFFFFFF"), font("<b/>", size=14), font("<b/>"), font(size=9, color="FF7F7F7F")]
    fills = ['<fill><patternFill patternType="none"/></fill>', '<fill><patternFill patternType="gray125"/></fill>',
             fill("FF1F4E78"), fill("FFFFF2CC"), fill("FFF2F2F2")]
    xfs = [
        '<xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/>',  # 0 기본
        '<xf numFmtId="0" fontId="2" fillId="0" borderId="0" xfId="0" applyFont="1"/>',  # 1 제목
        xf(1, 2, 1, "center"),   # 2 표 머리글
        xf(0, 0, 1),             # 3 본문
        xf(0, 0, 1, "center"),   # 4 본문(가운데)
        xf(0, 3, 1, num_fmt=49),  # 5 답변 칸: 날짜·숫자를 입력해도 글자로 남도록 텍스트 서식
        xf(4, 4, 1),             # 6 관리용 칸
        xf(3, 4, 1),             # 7 안내 시트 항목명
        '<xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0" applyAlignment="1">'
        '<alignment vertical="top" wrapText="1"/></xf>',  # 8 안내 문장
    ]
    return (f'{XML_HEAD}<styleSheet xmlns="{NS_MAIN}">'
            f'<fonts count="{len(fonts)}">{"".join(fonts)}</fonts>'
            f'<fills count="{len(fills)}">{"".join(fills)}</fills>'
            f'<borders count="2"><border><left/><right/><top/><bottom/><diagonal/></border>'
            f'<border>{border}<diagonal/></border></borders>'
            '<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>'
            f'<cellXfs count="{len(xfs)}">{"".join(xfs)}</cellXfs>'
            '<cellStyles count="1"><cellStyle name="표준" xfId="0" builtinId="0"/></cellStyles>'
            '</styleSheet>')


def guide_sheet_xml(sst: SharedStrings, meta: list[tuple[str, str]], title: str) -> str:
    rows = [f'<row r="1" ht="26" customHeight="1">{cell(sst, 0, 1, title, 1)}</row>']
    r = 3
    for key, value in meta:
        rows.append(f'<row r="{r}">{cell(sst, 0, r, key, 7)}{cell(sst, 1, r, value, 3)}</row>')
        r += 1
    r += 1
    rows.append(f'<row r="{r}">{cell(sst, 0, r, "작성 방법", 7)}{cell(sst, 1, r, "", 3)}</row>')
    for i, line in enumerate(GUIDE_LINES, 1):
        r += 1
        rows.append(f'<row r="{r}">{cell(sst, 0, r, str(i), 4)}{cell(sst, 1, r, line, 3)}</row>')
    return (f'{XML_HEAD}<worksheet xmlns="{NS_MAIN}">'
            '<sheetViews><sheetView workbookViewId="0" tabSelected="1" showGridLines="0"/></sheetViews>'
            '<sheetFormatPr defaultRowHeight="16.5"/>'
            '<cols><col min="1" max="1" width="16" customWidth="1"/><col min="2" max="2" width="96" customWidth="1"/></cols>'
            f'<sheetData>{"".join(rows)}</sheetData>'
            '<pageMargins left="0.5" right="0.5" top="0.6" bottom="0.6" header="0.3" footer="0.3"/>'
            '</worksheet>')


def question_sheet_xml(sst: SharedStrings, questions: list[dict]) -> str:
    last_col = col_letter(len(COLUMNS) - 1)
    cols = "".join(f'<col min="{i}" max="{i}" width="{width}" customWidth="1"/>'
                   for i, (_, _, width, _) in enumerate(COLUMNS, 1))
    header = "".join(cell(sst, i, 1, title, 2) for i, (_, title, _, _) in enumerate(COLUMNS))
    rows = [f'<row r="1" ht="30" customHeight="1">{header}</row>']
    for r, q in enumerate(questions, 2):
        cells = "".join(cell(sst, i, r, q.get(key, ""), style) for i, (key, _, _, style) in enumerate(COLUMNS))
        rows.append(f'<row r="{r}">{cells}</row>')
    last_row = len(questions) + 1
    return (f'{XML_HEAD}<worksheet xmlns="{NS_MAIN}">'
            '<sheetPr><pageSetUpPr fitToPage="1"/></sheetPr>'
            '<sheetViews><sheetView workbookViewId="0">'
            '<pane xSplit="1" ySplit="1" topLeftCell="B2" activePane="bottomRight" state="frozen"/>'
            '</sheetView></sheetViews>'
            '<sheetFormatPr defaultRowHeight="16.5"/>'
            f'<cols>{cols}</cols>'
            f'<sheetData>{"".join(rows)}</sheetData>'
            f'<autoFilter ref="A1:{last_col}{last_row}"/>'
            '<pageMargins left="0.4" right="0.4" top="0.6" bottom="0.6" header="0.3" footer="0.3"/>'
            '<pageSetup paperSize="9" orientation="landscape" fitToWidth="1" fitToHeight="0"/>'
            '</worksheet>')


def write_xlsx(path: Path, title: str, meta: list[tuple[str, str]], questions: list[dict]) -> None:
    sst = SharedStrings()
    sheets = [guide_sheet_xml(sst, meta, title), question_sheet_xml(sst, questions)]
    names = [GUIDE_SHEET, QUESTION_SHEET]
    overrides = "".join(
        f'<Override PartName="/xl/worksheets/sheet{i}.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
        for i in range(1, len(sheets) + 1))
    content_types = (
        f'{XML_HEAD}<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/xl/workbook.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
        f'{overrides}'
        '<Override PartName="/xl/styles.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>'
        '<Override PartName="/xl/sharedStrings.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sharedStrings+xml"/>'
        '</Types>')
    root_rels = (
        f'{XML_HEAD}<Relationships xmlns="{NS_PKG_REL}">'
        f'<Relationship Id="rId1" Type="{NS_REL}/officeDocument" Target="xl/workbook.xml"/>'
        '</Relationships>')
    sheet_tags = "".join(f'<sheet name="{escape(n)}" sheetId="{i}" r:id="rId{i}"/>' for i, n in enumerate(names, 1))
    workbook = (
        f'{XML_HEAD}<workbook xmlns="{NS_MAIN}" xmlns:r="{NS_REL}">'
        f'<bookViews><workbookView/></bookViews><sheets>{sheet_tags}</sheets></workbook>')
    n = len(sheets)
    wb_rels = (
        f'{XML_HEAD}<Relationships xmlns="{NS_PKG_REL}">'
        + "".join(f'<Relationship Id="rId{i}" Type="{NS_REL}/worksheet" Target="worksheets/sheet{i}.xml"/>'
                  for i in range(1, n + 1))
        + f'<Relationship Id="rId{n + 1}" Type="{NS_REL}/styles" Target="styles.xml"/>'
        + f'<Relationship Id="rId{n + 2}" Type="{NS_REL}/sharedStrings" Target="sharedStrings.xml"/>'
        + '</Relationships>')

    tmp = path.with_suffix(path.suffix + ".tmp")
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", content_types)
        z.writestr("_rels/.rels", root_rels)
        z.writestr("xl/workbook.xml", workbook)
        z.writestr("xl/_rels/workbook.xml.rels", wb_rels)
        z.writestr("xl/styles.xml", styles_xml())
        for i, xml in enumerate(sheets, 1):
            z.writestr(f"xl/worksheets/sheet{i}.xml", xml)
        # 시트를 만들면서 문자열이 등록되므로 마지막에 쓴다
        z.writestr("xl/sharedStrings.xml", sst.xml())
    tmp.replace(path)


# ---------------------------------------------------------------------------
# 엑셀 읽기
# ---------------------------------------------------------------------------

def parse_xml(raw: bytes):
    """엑셀 내부 XML을 해석한다. 정상적인 xlsx에는 DTD가 없으므로, 엔티티 확장 공격을 막기 위해 DTD 선언이 있으면 거부한다."""
    if b"<!DOCTYPE" in raw or b"<!ENTITY" in raw:
        raise ValueError("DTD 선언이 포함된 XML은 읽지 않습니다.")
    return ET.fromstring(raw)


def local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def children(node, name: str):
    return [c for c in node if local(c.tag) == name]


def string_item_text(node) -> str:
    """<si> 또는 <is>의 글자를 모은다. 한글 엑셀이 덧붙이는 윗주(rPh)는 제외한다."""
    parts = []
    for child in node:
        tag = local(child.tag)
        if tag == "t":
            parts.append(child.text or "")
        elif tag == "r":
            parts.extend(t.text or "" for t in children(child, "t"))
    return "".join(parts)


def read_workbook(path: Path) -> dict[str, list[list[str]]]:
    """시트 이름 → 행 목록(각 행은 열 순서대로 채운 문자열 목록)."""
    with zipfile.ZipFile(path) as z:
        names = set(z.namelist())
        shared: list[str] = []
        if "xl/sharedStrings.xml" in names:
            shared = [string_item_text(si) for si in children(parse_xml(z.read("xl/sharedStrings.xml")), "si")]
        rels = {}
        if "xl/_rels/workbook.xml.rels" in names:
            for rel in parse_xml(z.read("xl/_rels/workbook.xml.rels")):
                target = rel.get("Target", "")
                rels[rel.get("Id")] = target.lstrip("/") if target.startswith("/") else "xl/" + target
        result: dict[str, list[list[str]]] = {}
        wb = parse_xml(z.read("xl/workbook.xml"))
        for sheets in children(wb, "sheets"):
            for sheet in sheets:
                rid = next((v for k, v in sheet.attrib.items() if local(k) == "id"), None)
                part = rels.get(rid)
                if not part or part not in names:
                    continue
                rows: list[list[str]] = []
                root = parse_xml(z.read(part))
                for data in children(root, "sheetData"):
                    for row in children(data, "row"):
                        values: list[str] = []
                        for i, c in enumerate(children(row, "c")):
                            idx = col_index(c.get("r")) if c.get("r") else i
                            kind = c.get("t")
                            v = next(iter(children(c, "v")), None)
                            if kind == "inlineStr":
                                text = "".join(string_item_text(n) for n in children(c, "is"))
                            elif v is None or v.text is None:
                                text = ""
                            elif kind == "s":
                                text = shared[int(v.text)] if int(v.text) < len(shared) else ""
                            else:
                                text = v.text
                            while len(values) <= idx:
                                values.append("")
                            values[idx] = clean(text)
                        rows.append(values)
                result[nfc(sheet.get("name", ""))] = rows
        return result


def find_header(rows: list[list[str]]) -> tuple[int, dict[str, int]] | None:
    """앞쪽 20행에서 '질문'과 '답변' 열이 함께 있는 머리글 행을 찾는다."""
    for r, row in enumerate(rows[:20]):
        mapping: dict[str, int] = {}
        for i, value in enumerate(row):
            key = HEADER_KEYS.get(re.sub(r"\(.*?\)", "", value).strip())
            if key and key not in mapping:
                mapping[key] = i
        if "question" in mapping and "answer" in mapping:
            return r, mapping
    return None


def read_questionnaire(path: Path) -> dict:
    book = read_workbook(path)
    target = None
    # 시트 이름이 바뀌었을 수 있으므로 머리글이 맞는 시트를 차례로 찾는다
    for name in [QUESTION_SHEET] + [n for n in book if n != QUESTION_SHEET]:
        if name in book and (found := find_header(book[name])):
            target = (name, *found)
            break
    if not target:
        raise ValueError("'질문'과 '답변' 열이 있는 시트를 찾지 못했습니다.")
    name, header_row, mapping = target

    meta = {}
    for row in book.get(GUIDE_SHEET, []):
        if len(row) >= 2 and row[0] and row[1] and not row[0].isdigit():
            meta[row[0]] = row[1]

    questions = []
    extra = 0
    for row in book[name][header_row + 1:]:
        item = {key: (row[i] if i < len(row) else "") for key, i in mapping.items()}
        for key, *_ in COLUMNS:
            item.setdefault(key, "")
        if not item["question"] and not item["answer"] and not item["note"]:
            continue
        if not item["id"]:
            # 인수자나 인계자가 표 아래에 직접 추가한 행
            extra += 1
            item["id"] = f"추가-{extra}"
        item["answered"] = bool(item["answer"])
        questions.append(item)
    answered = sum(q["answered"] for q in questions)
    return {
        "file": nfc(path.name),
        "sheet": name,
        "meta": meta,
        "summary": {"total": len(questions), "answered": answered, "unanswered": len(questions) - answered},
        "questions": questions,
    }


# ---------------------------------------------------------------------------
# 명령
# ---------------------------------------------------------------------------

def cmd_build(args) -> int:
    spec = json.loads(Path(args.spec).read_text(encoding="utf-8-sig"))
    giver = clean(spec.get("handover_from"))
    if not giver:
        print("스펙에 인계자 이름(handover_from)이 없습니다.")
        return 1
    raw = spec.get("questions") or []
    questions = []
    for n, q in enumerate(raw, 1):
        item = {key: clean(q.get(key)) for key, *_ in COLUMNS}
        if not item["question"]:
            print(f"{n}번째 항목에 질문(question)이 없습니다.")
            return 1
        item["priority"] = item["priority"] or "중"
        if item["priority"] not in PRIORITIES:
            print(f"{n}번째 항목의 중요도(priority)는 {'·'.join(PRIORITIES)} 가운데 하나여야 합니다: {item['priority']}")
            return 1
        item["id"] = item["id"] or f"Q-{n:03d}"
        item["answer"], item["note"] = "", ""
        questions.append(item)
    if not questions:
        print("스펙에 질문(questions)이 없습니다.")
        return 1
    ids = [q["id"] for q in questions]
    if len(set(ids)) != len(ids):
        print("질문 번호(id)가 중복되었습니다.")
        return 1

    try:
        written = parse_date(spec.get("date"))
        due = parse_date(spec["due"]).isoformat() if spec.get("due") else ""
    except ValueError:
        print("날짜(date, due)는 YYYY-MM-DD 형식으로 적어야 합니다.")
        return 1
    out_dir = Path(args.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    name = f"{written:%y%m%d} {giver} {FILE_SUFFIX}.xlsx"
    path = out_dir / name
    if path.exists() and not args.force:
        print(f"같은 이름의 질문지가 이미 있습니다: {path}")
        print("이미 인계자에게 보낸 파일일 수 있으므로 덮어쓰지 않았습니다. 다시 만들려면 --force를 붙이십시오.")
        return 1

    title = f"{giver} 업무인계인수 질문지"
    counts = {p: sum(q["priority"] == p for q in questions) for p in PRIORITIES}
    meta = [
        ("인계자", giver),
        ("인수자", clean(spec.get("handover_to"))),
        ("작성일", written.isoformat()),
        ("회신 요청일", due),
        ("질문 수", f"{len(questions)}개 (" + ", ".join(f"{p} {counts[p]}" for p in PRIORITIES) + ")"),
        ("인수인계 건", clean(spec.get("package"))),
    ]
    write_xlsx(path, title, [(k, v) for k, v in meta if v], questions)
    print(f"질문지를 만들었습니다: {path}")
    print(f"질문 {len(questions)}개 (" + ", ".join(f"중요도 {p} {counts[p]}" for p in PRIORITIES) + ")")
    return 0


def cmd_read(args) -> int:
    path = Path(args.file)
    if not path.is_file():
        print(f"파일이 없습니다: {path}")
        return 1
    try:
        data = read_questionnaire(path)
    except (zipfile.BadZipFile, KeyError, ET.ParseError, ValueError) as exc:
        print(f"질문지를 읽지 못했습니다: {exc}")
        print("xlsx가 아닌 형식(.xls, .hwp 등)으로 회신받았다면 kordoc으로 변환해 내용을 확인하십시오.")
        return 1
    text = json.dumps(data, ensure_ascii=False, indent=2)
    if args.json:
        Path(args.json).write_text(text, encoding="utf-8")
        s = data["summary"]
        print(f"질문 {s['total']}개 중 답변 {s['answered']}개, 미회신 {s['unanswered']}개")
        print(f"JSON: {args.json}")
    else:
        print(text)
    return 0


def cmd_list(args) -> int:
    folder = Path(args.dir)
    files = sorted(p for p in folder.glob("*.xlsx") if not p.name.startswith(("~$", "."))) if folder.is_dir() else []
    if not files:
        print(f"질문지가 없습니다: {folder}")
        return 0
    for p in files:
        modified = datetime.fromtimestamp(p.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
        try:
            s = read_questionnaire(p)["summary"]
            state = f"질문 {s['total']} · 답변 {s['answered']} · 미회신 {s['unanswered']}"
        except (zipfile.BadZipFile, KeyError, ET.ParseError, ValueError) as exc:
            state = f"읽기 실패({exc})"
        print(f"{nfc(p.name)}  |  {state}  |  수정 {modified}")
    return 0


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description="업무인수인계 질문지(엑셀)를 만들고 회신받은 답변을 읽습니다.")
    sub = ap.add_subparsers(dest="command", required=True)

    b = sub.add_parser("build", help="질문 목록(JSON)으로 질문지 엑셀 만들기")
    b.add_argument("--spec", required=True, help="질문 목록 JSON 파일")
    b.add_argument("--out-dir", default=str(DEFAULT_DIR), help="질문지 폴더")
    b.add_argument("--force", action="store_true", help="같은 이름의 질문지가 있어도 덮어쓰기")
    b.set_defaults(func=cmd_build)

    r = sub.add_parser("read", help="회신받은 질문지에서 질문과 답변 읽기")
    r.add_argument("file", help="질문지 엑셀 파일")
    r.add_argument("--json", help="결과를 저장할 JSON 파일(생략하면 화면에 출력)")
    r.set_defaults(func=cmd_read)

    ls = sub.add_parser("list", help="질문지 폴더의 파일별 답변 현황 보기")
    ls.add_argument("--dir", default=str(DEFAULT_DIR), help="질문지 폴더")
    ls.set_defaults(func=cmd_list)

    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
