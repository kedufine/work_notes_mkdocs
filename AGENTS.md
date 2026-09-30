# 프로젝트 지침

전임자의 인수인계 자료(HWP·HWPX·PDF·DOCX·XLSX·XLS·PPTX·이미지 등)를 읽어 마크다운으로 변환하고, MkDocs 사이트에 업무 주제별로 등록하는 프로젝트입니다.

## 폴더

| 경로 | 역할 |
| :--- | :--- |
| `1. 인수인계 자료 원본/` | 사용자가 받은 자료를 그대로 넣는 곳. **읽기만 하고 수정·이동·삭제하지 않는다.** |
| `2. 변환 중간본/` | 변환 스크립트 산출물(`manifest.json`, `변환 보고서.md`, 파일별 마크다운). 다시 만들 수 있다. |
| `mkdocs/docs/handover/` | 정리된 인수인계 문서. |
| `mkdocs/mkdocs.yml` | 사이트 설정과 `nav`. |

원본과 중간본은 `.gitignore`로 제외한다.

## 작업별 스킬

| 작업 | 스킬 |
| :--- | :--- |
| 인수인계 원본 자료 변환·등록, 자료 추가·수정·삭제 반영 | `.agents/skills/handover-to-mkdocs/SKILL.md` |
| `mkdocs/docs/` 아래 `.md` 문서 작성·수정 | `.agents/skills/mkdocs-writing-guide/SKILL.md` |
| Mermaid 다이어그램 추가·수정 전 미리 렌더링 | `.agents/skills/pretty-mermaid/SKILL.md` (작성 규칙은 `mkdocs-writing-guide` 5.3절) |

## 필수 규칙

- 파일 읽기는 kordoc(HWP·HWPX·PDF·DOCX·XLS(X)·이미지)과 OfficeCLI(PPTX)를 사용한다. 원본을 하나씩 따로 열지 말고 `handover-to-mkdocs`의 변환 스크립트로 일괄 변환한다.
- 도구가 없으면 사용자에게 알린 뒤 설치 스크립트(`setup/setup-mac.sh`, `setup/setup-windows.ps1`)를 실행한다. 실패하면 `README.md` 2절의 수동 설치를 따른다. 원문 안내는 <https://github.com/chrisryugj/kordoc>, <https://github.com/iOfficeAI/OfficeCLI>이다.
- 변환 문서의 본문은 원문을 요약하지 않고 옮긴다. 에이전트가 쓰는 부분은 `요약`과 `인수인계 확인 사항`뿐이다.
- 이 사이트는 사용자 본인만 로컬에서 본다. 연락처 등 개인정보를 가리지 않고 원문 그대로 옮긴다.
- 모든 원본이 어떤 문서에 반영되었는지 `manifest.json`의 `published`로 추적한다.
- 문서를 추가·수정하면 `nav` 등록, 홈(`mkdocs/docs/index.md`) 최근 업데이트 갱신, `mkdocs build --strict` 통과까지 마친다.
- 사용자가 "실행해줘", "업무노트 실행해줘", "mkdocs 실행해줘" 등을 요청하면 로컬 개발 서버(`.venv/bin/mkdocs serve -f mkdocs/mkdocs.yml`, Windows는 `.venv\Scripts\mkdocs serve -f mkdocs\mkdocs.yml`)를 실행하고 브라우저 접속 주소(http://127.0.0.1:8000)를 안내한다.

## 공통

- 사용자에게 보이는 글, 문서, 커밋 메시지는 한국어로 쓴다.
- 이 파일과 각 `SKILL.md`의 내용이 어긋나면 `SKILL.md`의 상세 규정을 따르고, 사용자에게 알린다. 이를 이유로 작업을 중단하지 않는다.
