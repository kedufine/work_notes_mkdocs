# 프로젝트 지침

전임자의 인수인계 자료(HWP·HWPX·PDF·DOCX·XLSX·XLS·PPTX·이미지 등)를 읽어 마크다운으로 변환하고, MkDocs 사이트에 업무 주제별로 등록하는 프로젝트입니다.

## 폴더

| 경로 | 역할 |
| :--- | :--- |
| `1. RAW/` | 인수인계 자료 원본. 사용자가 받은 자료를 그대로 넣는 곳. **읽기만 하고 수정·이동·삭제하지 않는다.** |
| `2. 변환 중간본/` | 변환 스크립트 산출물(`manifest.json`, `변환 보고서.md`, 파일별 마크다운, `images/`). 다시 만들 수 있다. |
| `mkdocs/docs/handover/` | 정리된 인수인계 문서. 개요 페이지는 `handover/index.md`. |
| `mkdocs/docs/index.md` | 사이트 홈. 요약 표와 최근 업데이트 표가 있다. |
| `mkdocs/mkdocs.yml` | 사이트 설정과 `nav`. |
| `LICENSES/` | 사용 중인 서드파티 소프트웨어의 라이선스 전문(현재 Material for MkDocs). 원문을 그대로 두며, 빌드할 때 `mkdocs/hooks/licenses.py`가 사이트에 복사한다. |
| `setup/` | 전체 설치 스크립트(`setup-mac.sh`, `setup-windows.ps1`)와 사이트 실행 스크립트(`serve-mac.sh`, `serve-windows.ps1`). |

원본과 중간본은 `.gitignore`로 제외한다.

## 작업별 스킬

이 프로젝트의 스킬은 `.agents/skills/`에 있어 에이전트가 자동으로 불러오지 않을 수 있다. **작업을 시작하기 전에 해당 `SKILL.md`를 직접 읽고** 그 절차를 따른다.

| 작업 | 스킬 |
| :--- | :--- |
| 인수인계 원본 자료 변환·등록, 자료 추가·수정·삭제 반영 | `.agents/skills/handover-to-mkdocs/SKILL.md` |
| `mkdocs/docs/` 아래 `.md` 문서 작성·수정 | `.agents/skills/mkdocs-writing-guide/SKILL.md` |
| Mermaid 다이어그램 추가·수정 전 미리 렌더링 | `.agents/skills/pretty-mermaid/SKILL.md` (작성 규칙은 `mkdocs-writing-guide` 5.3절) |

인수인계 자료를 변환·등록할 때는 `handover-to-mkdocs`와 `mkdocs-writing-guide`를 함께 읽는다.

## 필수 규칙

- 파일 읽기는 kordoc(HWP·HWPX·PDF·DOCX·XLS(X)·이미지)과 OfficeCLI(PPTX)를 사용한다. 원본을 하나씩 따로 열지 말고 `handover-to-mkdocs`의 변환 스크립트로 일괄 변환한다.
- 사용자 PC에는 파이썬을 포함해 **아무 프로그램도 설치되어 있지 않을 수 있다**고 가정한다. 사이트는 프로젝트의 `.venv`에 설치된 Python, MkDocs, Material for MkDocs(`mkdocs-material`, 버전은 `mkdocs/requirements.txt`)가 있어야 동작하고, 변환은 Node.js, kordoc, OfficeCLI가 필요하다. 작업 전에 `convert.py --check`로 여섯 항목을 확인한다(절차는 `handover-to-mkdocs` 2절).
- 도구가 없으면 사용자에게 알린 뒤 설치 스크립트(`setup/setup-mac.sh`, `setup/setup-windows.ps1`)를 실행한다. 설치 스크립트는 Python과 Material for MkDocs까지 설치한다. 종료 코드 3이면 아래 "사용자 조치 절차"를 따르고, 종료 코드 1로 실패하면 `README.md` 2절의 수동 설치를 따른다. 원문 안내는 <https://github.com/chrisryugj/kordoc>, <https://github.com/iOfficeAI/OfficeCLI>이다.
- 변환 문서의 본문은 원문을 요약하지 않고 옮긴다. 에이전트가 쓰는 부분은 `요약`과 `인수인계 확인 사항`뿐이다.
- 이 사이트는 사용자 본인만 로컬에서 본다. 연락처 등 개인정보를 가리지 않고 원문 그대로 옮긴다.
- 변환된 모든 원본(`converted`·`empty`)이 어떤 문서에 반영되었는지 `manifest.json`의 `published`로 추적한다. 변환하지 못한 원본은 `handover/index.md`의 대응표에 상태와 조치 방법을 적는다.
- Windows에서 명령을 실행할 때도 경로는 `/`로 적는다(예: `.venv/Scripts/mkdocs`, `setup/serve-windows.ps1`). 에이전트의 셸이 Git Bash이면 `\`가 이스케이프 문자로 처리되어 경로가 깨지고, PowerShell은 `/`도 경로로 인식한다.
- 설치 스크립트가 Node.js·kordoc·OfficeCLI를 설치한 직후에는 에이전트 셸의 PATH가 갱신되지 않아 `node`, `npm`을 찾지 못할 수 있다. `convert.py`는 알려진 설치 경로를 스스로 찾으므로 그대로 실행하면 되고, 에이전트가 직접 `node`·`npm`을 실행해야 하면 전체 경로(macOS `/opt/homebrew/bin/node`, Windows `"C:/Program Files/nodejs/node.exe"`)를 사용한다. 이를 이유로 사용자에게 에이전트를 다시 시작하라고 요청하지 않는다.
- 문서를 추가·수정하면 `nav` 등록, 홈(`mkdocs/docs/index.md`) 최근 업데이트 갱신, 빌드 검증까지 마친다. 빌드 검증 명령은 다음과 같다. 통과 기준은 `mkdocs-writing-guide` 6절을 따른다.
    - macOS: `.venv/bin/mkdocs build --strict -f mkdocs/mkdocs.yml`
    - Windows: `.venv/Scripts/mkdocs build --strict -f mkdocs/mkdocs.yml`
- 사용자가 "실행해줘", "업무노트 실행해줘", "mkdocs 실행해줘" 등을 요청하면, 사용자가 아무것도 하지 않아도 사이트가 열리도록 다음 순서로 진행한다. 필요한 프로그램이 없으면 확인을 묻지 말고 "필요한 프로그램을 자동으로 설치합니다"라고만 알린 뒤 설치한다.
    1. **준비** (포그라운드, 제한 시간 10분): 사이트에 필요한 Python·MkDocs·Material for MkDocs를 확인하고 없으면 설치한다. 관리자 권한 없이 설치하므로 암호 입력이나 UAC 창이 뜨지 않는다.
        - macOS: `bash setup/serve-mac.sh --prepare`
        - Windows: `powershell -NoProfile -ExecutionPolicy Bypass -File setup/serve-windows.ps1 -Prepare`
    2. **실행** (백그라운드): 같은 스크립트를 옵션 없이 실행한다(macOS `bash setup/serve-mac.sh`, Windows `powershell -NoProfile -ExecutionPolicy Bypass -File setup/serve-windows.ps1`). 출력에 `Serving on`이 나오거나 <http://127.0.0.1:8000>이 응답하면 주소를 안내한다. `이미 8000 포트에서 실행 중입니다`가 나오면 새로 띄우지 않고 기존 주소를 안내한다.
    3. 종료 코드가 3이면 아래 "사용자 조치 절차"를 따른다.

## 사용자 조치 절차

설치·실행 스크립트(`setup/` 아래 네 개)는 AI가 대신할 수 없는 일(macOS 암호 입력, Windows 사용자 계정 컨트롤 승인, Microsoft Store 설치, 인터넷 연결 문제 등)을 만나면 `[사용자 조치 필요]`로 시작하는 안내를 출력하고 **종료 코드 3**으로 끝난다.

1. 안내의 제목과 번호 매긴 단계를 **빠짐없이 그대로** 사용자에게 전달하고, 끝나면 "했어"라고 말해 달라고 요청한 뒤 작업을 멈춘다. 다른 설치 방법으로 우회하거나 `sudo` 암호를 묻지 않는다.
2. 사용자가 "했어", "완료", "설치했어" 등으로 답하면, **멈췄던 스크립트를 같은 명령으로 다시 실행**한다. 스크립트는 이미 끝난 단계를 건너뛰므로 멈춘 지점부터 이어진다.
3. 다시 실행해 성공하면 원래 요청(예: 사이트 실행, 자료 변환)을 끝까지 마친다. 다시 종료 코드 3이 나오면 새 안내로 1번을 반복한다.
4. 종료 코드 1은 사용자 조치가 아닌 실패다. 출력된 오류를 확인해 해결하고, 해결하지 못하면 `README.md` 5절(문제 해결)과 2절(수동 설치)을 참고한다.
5. Windows 설치 스크립트(`setup-windows.ps1`)는 Git·Node.js를 설치할 때 UAC 창을 띄운다. 실행하기 전에 "잠시 후 '사용자 계정 컨트롤' 창이 뜨면 '예'를 눌러 주세요"라고 먼저 알린다.

## 공통

- 사용자에게 보이는 글, 문서, 커밋 메시지는 한국어로 쓴다.
- 이 파일과 각 `SKILL.md`의 내용이 어긋나면 `SKILL.md`의 상세 규정을 따르고, 사용자에게 알린다. 이를 이유로 작업을 중단하지 않는다.
