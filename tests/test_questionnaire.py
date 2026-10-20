"""questionnaire.py(3·4단계 질문지)의 작성과 회신 읽기를 검증한다.

실행(프로젝트 루트에서): .venv/bin/python -m unittest discover -s tests
"""

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / ".agents/skills/handover-questionnaire/scripts/questionnaire.py"

spec = importlib.util.spec_from_file_location("questionnaire", SCRIPT)
questionnaire = importlib.util.module_from_spec(spec)
spec.loader.exec_module(questionnaire)


class QuestionnaireTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.base = Path(self._tmp.name)
        self.out_dir = self.base / "q"

    def tearDown(self):
        self._tmp.cleanup()

    def build(self, questions, *extra):
        spec_path = self.base / "spec.json"
        spec_path.write_text(json.dumps({
            "handover_from": "홍길동", "handover_to": "김인수", "date": "2026-10-20",
            "due": "2026-10-27", "package": "시험 건", "questions": questions,
        }, ensure_ascii=False), encoding="utf-8")
        return subprocess.run(
            [sys.executable, str(SCRIPT), "build", "--spec", str(spec_path), "--out-dir", str(self.out_dir), *extra],
            capture_output=True, text=True, encoding="utf-8", timeout=60,
        )

    def test_build_and_read_round_trip(self):
        res = self.build([
            {"category": "예산", "question": '<특수문자> & "따옴표"\n둘째 줄', "priority": "상"},
            {"question": "두 번째 질문"},
        ])
        self.assertEqual(res.returncode, 0, res.stdout)
        path = self.out_dir / "261020 홍길동 업무인계인수 질문지.xlsx"
        data = questionnaire.read_questionnaire(path)
        self.assertEqual(data["meta"]["인계자"], "홍길동")
        self.assertEqual(data["meta"]["회신 요청일"], "2026-10-27")
        self.assertEqual([q["id"] for q in data["questions"]], ["Q-001", "Q-002"])
        self.assertEqual(data["questions"][0]["question"], '<특수문자> & "따옴표"\n둘째 줄')
        # 중요도를 비우면 '중'이 된다
        self.assertEqual(data["questions"][1]["priority"], "중")
        self.assertEqual(data["summary"], {"total": 2, "answered": 0, "unanswered": 2})

    def test_refuses_to_overwrite_sent_questionnaire(self):
        self.assertEqual(self.build([{"question": "질문"}]).returncode, 0)
        self.assertEqual(self.build([{"question": "질문"}]).returncode, 1)
        self.assertEqual(self.build([{"question": "질문"}], "--force").returncode, 0)

    def test_rejects_invalid_spec(self):
        self.assertEqual(self.build([{"question": "질문", "priority": "최상"}]).returncode, 1)
        self.assertEqual(self.build([{"category": "질문 없음"}]).returncode, 1)
        self.assertEqual(self.build([{"id": "Q-1", "question": "가"}, {"id": "Q-1", "question": "나"}]).returncode, 1)

    def test_reads_answers_and_added_rows(self):
        # 인계자가 답변을 적고, 표 아래에 행을 하나 추가해 회신한 파일을 흉내 낸다
        path = self.base / "회신.xlsx"
        questions = [
            {"id": "Q-001", "question": "질문 1", "priority": "상", "answer": "2026-11-01까지 제출", "note": "첨부.hwp"},
            {"id": "Q-002", "question": "질문 2", "priority": "중"},
            {"question": "인계자가 추가한 내용", "answer": "보충 설명"},
        ]
        questionnaire.write_xlsx(path, "질문지", [("인계자", "홍길동")], questions)
        data = questionnaire.read_questionnaire(path)
        self.assertEqual(data["summary"], {"total": 3, "answered": 2, "unanswered": 1})
        self.assertEqual(data["questions"][0]["answer"], "2026-11-01까지 제출")
        self.assertEqual(data["questions"][0]["note"], "첨부.hwp")
        self.assertEqual(data["questions"][2]["id"], "추가-1")

    def test_rejects_xml_with_dtd(self):
        with self.assertRaises(ValueError):
            questionnaire.parse_xml(b'<?xml version="1.0"?><!DOCTYPE x [<!ENTITY a "b">]><x>&a;</x>')


if __name__ == "__main__":
    unittest.main()
