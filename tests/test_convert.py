"""convert.py(1단계 변환)의 증분 갱신 흐름을 검증한다.

kordoc·OfficeCLI 없이 돌아가도록 텍스트·CSV·미지원 형식만 쓴다.
실행(프로젝트 루트에서): .venv/bin/python -m unittest discover -s tests
"""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / ".agents/skills/handover-to-mkdocs/scripts/convert.py"


class ConvertTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        base = Path(self._tmp.name)
        self.raw = base / "raw"
        self.out = base / "out"
        (self.raw / "sub").mkdir(parents=True)
        (self.raw / "표.csv").write_text('구분,값\n1,"a|b"\n', encoding="utf-8")
        (self.raw / "sub" / "메모.txt").write_bytes("한글 메모".encode("cp949"))
        (self.raw / "통계.cell").write_bytes(b"dummy")

    def tearDown(self):
        self._tmp.cleanup()

    def run_convert(self):
        res = subprocess.run(
            [sys.executable, str(SCRIPT), "--source", str(self.raw), "--out", str(self.out)],
            capture_output=True, text=True, encoding="utf-8", timeout=600,
        )
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
        return res.stdout

    def manifest(self):
        data = json.loads((self.out / "manifest.json").read_text(encoding="utf-8"))
        return {e["source"]: e for e in data["files"].values()}

    def test_converts_text_and_reports_unsupported(self):
        self.run_convert()
        files = self.manifest()
        self.assertEqual(files["표.csv"]["status"], "converted")
        self.assertEqual(files["sub/메모.txt"]["status"], "converted")
        # CP949 텍스트를 읽고, 표 안의 |는 이스케이프한다
        memo = (self.out / files["sub/메모.txt"]["output"]).read_text(encoding="utf-8")
        self.assertIn("한글 메모", memo)
        table = (self.out / files["표.csv"]["output"]).read_text(encoding="utf-8")
        self.assertIn("a\\|b", table)
        # 한셀 파일은 다시 저장하라는 구체적인 안내가 붙는다
        self.assertEqual(files["통계.cell"]["status"], "unsupported")
        self.assertIn(".xlsx", files["통계.cell"]["hint"])
        report = (self.out / "변환 보고서.md").read_text(encoding="utf-8")
        self.assertIn("통계.cell", report)

    def test_skips_unchanged_files(self):
        self.run_convert()
        stdout = self.run_convert()
        self.assertEqual(stdout.count("건너뜀"), 3)

    def test_marks_changed_and_removed_sources(self):
        self.run_convert()
        # 2단계에서 문서에 반영했다고 기록한다
        path = self.out / "manifest.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        for e in data["files"].values():
            e["published"] = ["handover/test/index.md"]
        path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        removed_output = self.out / self.manifest()["sub/메모.txt"]["output"]

        (self.raw / "표.csv").write_text("구분,값\n2,c\n", encoding="utf-8")
        (self.raw / "sub" / "메모.txt").unlink()
        self.run_convert()

        files = self.manifest()
        self.assertTrue(files["표.csv"]["needs_republish"])
        self.assertEqual(files["sub/메모.txt"]["status"], "removed")
        self.assertTrue(files["sub/메모.txt"]["needs_republish"])
        # 삭제된 원본의 중간본은 지워져 출처로 쓰이지 않는다
        self.assertFalse(removed_output.exists())
        self.assertFalse(files["통계.cell"]["needs_republish"])

        # 에이전트가 문서를 고친 뒤 끈 표시는 다시 실행해도 유지된다
        data = json.loads(path.read_text(encoding="utf-8"))
        for e in data["files"].values():
            e["needs_republish"] = False
        path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        self.run_convert()
        self.assertFalse(any(e["needs_republish"] for e in self.manifest().values()))


if __name__ == "__main__":
    unittest.main()
