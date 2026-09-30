---
name: handover-to-mkdocs
description: >-
  '1. 인수인계 자료 원본' 폴더에 들어온 인수인계 자료(HWP·HWPX·PDF·DOCX·XLSX·XLS·PPTX·이미지·CSV 등)를
  kordoc과 OfficeCLI로 모두 읽어 마크다운으로 변환하고 MkDocs 사이트에 주제별로 등록할 때 사용합니다.
  "인수인계 자료 추가", "자료 추가됐어", "새 업무 반영" 같은 요청이나,
  원본 폴더의 파일이 추가·수정·삭제된 뒤 사이트를 갱신할 때 활용합니다.
---

# 인수인계 자료 변환·등록

인수인계 자료 원본을 빠짐없이 읽어 MkDocs 문서로 옮기는 절차입니다. 원본은 폴더 구조가 정리되어 있지 않고 파일 수가 많을 수 있으므로, **기계적 변환(1단계)과 주제별 정리·등록(2단계)을 분리**하고 모든 진행 상태를 `manifest.json`에 기록합니다.

문서 본문의 작성 규칙(제목 구조, 표, 알림 상자, `nav`, 홈 갱신, 빌드 검증)은 `.agents/skills/mkdocs-writing-guide/SKILL.md`를 따릅니다. 이 스킬은 그 규칙 위에서 인수인계 자료에만 해당하는 절차를 정합니다.

---

## 1. 폴더와 산출물

| 경로 | 역할 | Git |
| :--- | :--- | :--- |
| `1. 인수인계 자료 원본/` | 사용자가 받은 자료를 그대로 넣는 곳입니다. **에이전트는 이 폴더의 파일을 수정·이동·삭제하지 않습니다.** | 제외 |
| `2. 변환 중간본/` | 1단계 스크립트가 만드는 원문 마크다운, `manifest.json`, `변환 보고서.md`입니다. 언제든 다시 만들 수 있습니다. | 제외 |
| `mkdocs/docs/handover/` | 2단계에서 정리한 공개용 문서입니다. | 포함 |

원본과 중간본은 대용량 파일이고 언제든 다시 만들 수 있으므로 `.gitignore`로 제외합니다. 사이트는 사용자 본인만 로컬에서 보는 용도이므로, **개인정보(연락처, 이름 등)를 가리지 않고 원문 그대로 옮깁니다.**

---

## 2. 사전 점검

작업을 시작할 때마다 먼저 도구를 확인합니다.

```bash
.venv/bin/python .agents/skills/handover-to-mkdocs/scripts/convert.py --check       # macOS
.venv\Scripts\python .agents\skills\handover-to-mkdocs\scripts\convert.py --check   # Windows
```

이 문서의 이후 명령은 macOS 경로로 적습니다. Windows에서는 `.venv\Scripts\python`과 `\` 경로 구분자를 사용합니다. 변환 스크립트는 표준 라이브러리만 쓰므로, `.venv`가 아직 없으면 `--check`는 시스템 파이썬(`python3`, Windows는 `py`)으로 실행합니다.

사용자 PC에는 **아무 프로그램도 설치되어 있지 않을 수 있다**고 가정합니다. 문서 사이트는 `.venv`에 설치된 Python, MkDocs, Material for MkDocs(`mkdocs-material`)가 있어야 빌드·실행되고, 변환은 Node.js, kordoc, OfficeCLI가 있어야 합니다. `--check`는 이 여섯 항목(`python`, `mkdocs`, `mkdocs-material`, `node`, `kordoc`, `officecli`)을 모두 확인합니다.

- 여섯 항목 가운데 `없음`이 하나라도 있으면, 사용자에게 알린 뒤 설치 스크립트를 실행합니다. 설치 스크립트는 없는 프로그램만 설치합니다.
- 시스템 파이썬도 없어서 `--check`를 실행할 수 없으면(`python3`·`py`를 찾을 수 없음, 또는 Windows에서 `python`을 입력하면 Microsoft Store가 열림), 확인을 건너뛰고 바로 설치 스크립트를 실행합니다. 설치 스크립트가 파이썬부터 설치합니다.

- macOS: `bash setup/setup-mac.sh`
- Windows: `powershell -NoProfile -ExecutionPolicy Bypass -File setup\setup-windows.ps1` (`-Pause`는 넘기지 않습니다. 넘기면 끝에서 Enter 입력을 기다리며 멈춥니다.)

에이전트가 대신할 수 없는 일(macOS에서 Homebrew 설치에 필요한 암호 입력, Windows의 사용자 계정 컨트롤 승인·Microsoft Store 설치, 인터넷 연결 문제)을 만나면, 설치 스크립트가 `[사용자 조치 필요]` 안내를 출력하고 종료 코드 3으로 끝납니다. 이때는 `AGENTS.md`의 "사용자 조치 절차"대로 안내를 그대로 전달하고 멈춘 뒤, 사용자가 "했어"라고 하면 같은 명령을 다시 실행해 이어서 진행합니다. Windows 설치 스크립트를 실행하기 전에는 UAC 창이 뜰 수 있다고 먼저 알립니다.

설치 스크립트가 실패하면 `README.md` 2절(수동 설치)의 해당 단계를 따릅니다. kordoc을 직접 설치할 때는 OCR 엔진이 빠지지 않도록 `npm install -g kordoc --allow-scripts=onnxruntime-node,protobufjs`를 사용합니다. 원문 안내는 <https://github.com/chrisryugj/kordoc>, <https://github.com/iOfficeAI/OfficeCLI>에 있습니다. 설치 뒤에도 `없음`이 나오면 새 터미널에서 다시 확인합니다.

---

## 3. 1단계: 원본 전체를 중간본으로 변환

```bash
.venv/bin/python .agents/skills/handover-to-mkdocs/scripts/convert.py --dry-run   # 대상 목록과 처리 경로만 확인
.venv/bin/python .agents/skills/handover-to-mkdocs/scripts/convert.py             # 변환 실행
```

스크립트는 원본 폴더를 하위 폴더까지 모두 훑고, 형식에 따라 다음 도구로 변환합니다.

| 형식 | 도구 | 비고 |
| :--- | :--- | :--- |
| `.hwp` `.hwpx` `.hwpml` `.hml` | kordoc | 표·병합 셀 보존 |
| `.pdf` | kordoc | 스캔 PDF(`IMAGE_BASED_PDF`)는 OCR을 켜고 자동 재시도 |
| `.docx` `.xlsx` | kordoc → 실패 시 OfficeCLI | |
| `.xls` `.docm` `.xlsm` | kordoc | |
| `.pptx` | OfficeCLI | kordoc은 PPTX를 지원하지 않음. 슬라이드별 `## 슬라이드 N` 제목으로 변환 |
| `.png` `.jpg` `.jpeg` `.webp` | kordoc | 내장 OCR |
| `.txt` `.md` `.csv` `.tsv` | 스크립트 | UTF-8·CP949 자동 판별, CSV는 표로 변환(최대 500행) |
| `.doc` `.ppt` `.rtf`, 압축 파일 등 | 변환 안 함 | 보고서에 조치 방법(다시 저장, 압축 해제)을 기록 |

- `~$`로 시작하는 Office 잠금 파일, 숨김 파일, `Thumbs.db`, `desktop.ini`는 제외합니다.
- 중간본은 `2. 변환 중간본/<8자리 ID>_<원본 파일명>.md`로 평탄하게 저장합니다. ID는 원본 상대 경로의 해시이므로 같은 파일은 항상 같은 ID를 받습니다. kordoc이 추출한 그림은 `2. 변환 중간본/images/<중간본 이름>/`에 저장됩니다.
- 원본 해시가 바뀌지 않은 파일은 다시 변환하지 않습니다. 중간에 끊겨도 같은 명령을 다시 실행하면 이어서 진행됩니다. 실패한 파일은 매번 다시 시도합니다.
- 파일이 많으면 명령을 백그라운드로 실행하고 끝날 때까지 기다립니다. 진행 중에 파일을 하나씩 따로 변환하지 않습니다.

### 3.1 manifest.json 필드

최상위에는 `version`, `updated_at`(마지막 실행 시각), `tools`(도구 버전), `files`(원본 ID → 항목)가 있습니다. 각 항목의 필드는 다음과 같습니다.

| 필드 | 뜻 |
| :--- | :--- |
| `id` | 원본 상대 경로의 해시 8자리. `files`의 키와 같습니다. |
| `source`, `ext`, `size`, `sha256` | 원본 폴더 기준 상대 경로(NFC), 확장자, 크기, 내용 해시 |
| `status` | `converted`, `empty`, `failed`, `unsupported`, `removed` |
| `tool`, `error_code`, `error`, `hint` | 사용한 도구, 실패 코드, 오류 원문, 조치 방법 |
| `output`, `images`, `chars` | 중간본 파일명, 그림 폴더(`2. 변환 중간본/` 기준), 중간본 글자 수 |
| `ocr` | 스캔 PDF라서 OCR로 다시 변환했으면 `true` |
| `modified` | 원본 파일의 수정일 |
| `published` | 이 원본을 반영한 MkDocs 문서 경로 목록(**2단계에서 에이전트가 기록**) |
| `needs_republish` | 원본이 바뀌거나 삭제되어 문서를 고쳐야 하면 `true`(**반영 후 에이전트가 `false`로 변경**) |

스크립트는 재실행해도 `published`와 `needs_republish`를 보존합니다. 에이전트가 고치는 필드는 이 두 개뿐입니다.

### 3.2 변환 결과 점검

`2. 변환 중간본/변환 보고서.md`를 읽고 다음을 사용자에게 보고합니다.

- 상태별 개수와 **조치가 필요한 파일**(실패, 미지원, 빈 결과) 목록과 조치 방법
- 사용자가 조치할 수 있는 항목(암호 해제, `.doc`→`.docx` 다시 저장, 압축 해제)이 있으면 조치 후 1단계를 다시 실행하도록 안내합니다. 이 항목 때문에 2단계를 멈추지는 않습니다.

---

## 4. 2단계: 주제별 정리와 MkDocs 등록

### 4.1 분류 설계 (처음 한 번)

1. `manifest.json`의 `source` 경로 전체와 각 중간본의 첫 부분(제목, 첫 30줄 정도)을 훑어 **업무 주제**를 파악합니다. 원본 폴더 구조가 주제와 맞으면 그대로 따르고, 뒤섞여 있으면 내용 기준으로 다시 묶습니다.
2. 대분류는 3~8개로 정합니다(예: `업무 개요`, `예산·회계`, `시스템 운영`, `민원·대외`, `정기 업무 일정`, `참고 자료`). 한 대분류에 문서가 15개를 넘으면 하위 분류(하위 폴더와 `nav` 하위 섹션)를 둡니다.
3. 분류안(대분류 이름, 영문 폴더명, 대략적인 문서 수)을 사용자에게 한 번 보여 주고 진행합니다. 사용자가 응답하지 않아도 되는 형태로 제시하고, 작업을 멈추지 않습니다.

### 4.2 문서 단위 결정

- 기본은 **원본 파일 1개 → 문서 1개**입니다.
- 같은 문서의 판본(`최종`, `최종2`, `수정본`, 날짜만 다른 사본)은 **최신본 하나로 문서를 만들고**, 나머지는 문서의 `원본 정보` 표에 함께 적습니다. 함께 적은 판본의 `published`에도 그 문서 경로를 넣습니다. 판본 판단은 파일명·수정일·내용 비교로 하고, 판본끼리 내용이 크게 다르면 차이를 `인수인계 확인 사항`의 변환 메모에 적습니다.
- 내용이 거의 없는 파일(양식 빈칸, 한두 줄 메모)은 같은 주제의 `기타 자료` 문서 하나에 모읍니다.
- 한 원본이 지나치게 길면(중간본 3,000줄 이상) 장 단위로 문서를 나눌 수 있습니다.
- 어떤 원본도 누락되지 않아야 합니다. 모든 `converted`·`empty` 항목은 최소 한 문서의 `published`에 들어가야 합니다.

### 4.3 문서 작성

- 파일 경로: `mkdocs/docs/handover/<대분류 영문 폴더>/<영문 소문자-하이픈>.md`. 한글 제목은 `nav`에서 지정합니다.
- 골격은 `mkdocs-writing-guide` 4.2절 **인수인계 변환 문서 골격**을 따릅니다.
- 본문은 중간본을 **요약하지 않고 옮깁니다.** 원문의 문장·수치·표를 바꾸지 않고, 다음만 정리합니다.
    - 제목 구조: 문서 H1은 하나만 두고, 원문 제목은 `##`·`###`으로 맞춥니다.
    - kordoc이 넣은 공문서 끝 표시(`끝.`), 머리글·바닥글 반복, 빈 줄 과다를 정리합니다.
    - 목록 들여쓰기를 공백 4칸으로 맞춥니다(가이드 2.5절).
    - 긴 표(500행 초과)는 앞부분만 두고 전체 행 수와 원본 경로를 알림 상자로 남깁니다.
- 그림: 중간본의 그림 링크는 `images/<중간본 이름>/image_001.png` 형태이고, 실제 파일은 `2. 변환 중간본/images/<중간본 이름>/`에 있습니다. 본문에 필요한 그림만 `mkdocs/docs/handover/<대분류>/images/<문서 파일명>/`으로 복사하고 링크를 고칩니다. 로고·도장·장식 그림은 옮기지 않고, 옮기지 않은 그림은 변환 메모에 적습니다.
- **연락처와 이름**: 담당자 연락처, 거래처 정보 같은 원문 내용은 가리거나 지우지 않고 그대로 옮깁니다. 인수인계에 필요한 정보입니다.
- 에이전트가 쓰는 부분은 `요약`과 `인수인계 확인 사항` 두 곳뿐이며, 원문에 근거한 내용만 적습니다.
- `nav`는 폴더 구조와 같게 `인수인계` 탭 아래에 대분류 섹션을 둡니다. `navigation.indexes`가 켜져 있으므로 개요 페이지는 섹션의 첫 항목에 제목 없이 적습니다.

```yaml
nav:
  - 홈: index.md
  - 인수인계:
      - handover/index.md
      - 예산·회계:
          - 연간 예산 계획: handover/budget/annual-plan.md
          - 기타 자료: handover/budget/misc.md
```

### 4.4 인수인계 개요 페이지

`mkdocs/docs/handover/index.md`를 만들고 파일이 추가될 때마다 갱신합니다. H1 아래 작성일·최종 수정일은 가이드 1절 2번을 따릅니다.

- 한 문장 요약과 `## 요약` 표(대분류, 문서 수, 주요 내용)
- `## 1. 원본 현황`: 전체 원본 수, 변환 완료·실패·미지원 개수, 마지막 변환 일시
- `## 2. 대분류별 문서 목록`: 대분류마다 `###` 소제목(대분류 이름)을 두고 문서 제목과 링크를 나열합니다. 홈 최근 업데이트의 `바로가기`가 이 소제목의 앵커(예: `### 예산·회계` → `handover/index.md#예산회계`)를 가리킵니다.
- `## 3. 원본 파일 대응표`: 원본 경로 → 문서 링크 전체 목록(원본 폴더 순서). 변환하지 못한 파일(`failed`, `unsupported`)은 상태와 조치 방법을 적습니다. `removed` 항목은 넣지 않습니다.
- `## 4. 인수인계 확인 사항 종합`: 각 문서의 확인 사항 가운데 중요한 것을 모은 결론 섹션

### 4.5 manifest 기록

문서를 만들거나 고칠 때마다 해당 원본 항목의 `published`에 문서 경로(`handover/...md`, `mkdocs/docs/` 기준)를 넣고 `needs_republish`를 `false`로 바꿉니다. 여러 문서를 한 번에 처리했다면 배치가 끝날 때 한 번에 기록해도 됩니다. 이 기록이 다음 작업의 이어하기 기준입니다.

- 변환 스크립트가 실행 중일 때는 `manifest.json`을 고치지 않습니다. 스크립트가 파일마다 manifest를 다시 쓰므로 고친 내용이 사라집니다.
- 항목이 많으면 손으로 JSON을 고치지 말고 짧은 파이썬 코드로 고칩니다. 원본 경로(`source`)로 항목을 찾습니다.

```bash
.venv/bin/python - <<'EOF'
import json, pathlib
p = pathlib.Path("2. 변환 중간본/manifest.json")
m = json.loads(p.read_text(encoding="utf-8"))
# 원본 경로 → 반영한 문서 경로 목록
done = {"예산/2025/예산 계획(최종).hwpx": ["handover/budget/annual-plan.md"]}
for e in m["files"].values():
    if e["source"] in done:
        e["published"] = sorted(set(e.get("published", [])) | set(done[e["source"]]))
        e["needs_republish"] = False
p.write_text(json.dumps(m, ensure_ascii=False, indent=2), encoding="utf-8")
EOF
```

Windows에서는 같은 코드를 스크래치 폴더에 `.py` 파일로 저장해 `.venv\Scripts\python`으로 실행합니다.

### 4.6 대량 처리 순서

파일이 많을 때는 대분류 하나씩 처리합니다. 대분류마다 문서 작성 → `nav` 등록 → `manifest` 기록 → 빌드 검증(`.venv/bin/mkdocs build --strict -f mkdocs/mkdocs.yml`)까지 끝내고 다음으로 넘어갑니다. 이렇게 하면 도중에 끊겨도 사이트가 항상 빌드 가능한 상태로 남습니다. `mkdocs.yml`의 `validation` 설정 때문에 `nav`에 빠진 문서나 없는 앵커로 가는 링크가 있으면 빌드가 실패하므로, 개요 페이지와 홈은 모든 대분류를 마친 뒤가 아니라 대분류마다 함께 갱신합니다.

---

## 5. 원본이 바뀌었을 때 (증분 갱신)

1. 1단계 명령을 다시 실행합니다. 새 파일만 변환되고, 바뀐 파일은 다시 변환되며, 사라진 파일은 `removed`로 표시됩니다.
2. `published`가 비어 있는 새 항목은 4.1의 분류에 맞춰 문서를 만들거나 기존 문서에 합칩니다. 기존 분류에 맞지 않으면 새 대분류를 만듭니다.
3. `needs_republish: true`이고 `status`가 `converted`·`empty`인 항목은 반영된 문서를 새 중간본으로 고치고, 최종 수정일을 갱신합니다.
4. `needs_republish: true`이고 `status`가 `removed`인 항목은 다음처럼 처리합니다.
    - 그 원본만으로 이루어진 문서는 삭제하고 `nav`와 개요 페이지에서도 뺍니다.
    - 다른 원본과 함께 쓰인 문서는 해당 원본의 내용과 `원본 정보` 행만 뺍니다.
    - 처리가 끝나면 그 항목의 `published`를 빈 목록으로, `needs_republish`를 `false`로 바꿉니다.
5. 1단계에서 `failed`였다가 사용자가 조치해 `converted`가 된 항목은 새 항목과 같게 처리합니다.
6. 개요 페이지의 원본 현황과 대응표, 홈 최근 업데이트를 갱신합니다.

---

## 6. 완료 조건

- [ ] `convert.py --check`에서 여섯 항목(Python·MkDocs·Material for MkDocs·Node.js·kordoc·OfficeCLI)이 모두 확인되었다.
- [ ] 1단계가 끝났고 `변환 보고서.md`의 조치 필요 항목을 사용자에게 보고했다.
- [ ] 모든 `converted`·`empty` 원본이 어떤 문서의 `published`에 들어 있고, `needs_republish: true`인 항목이 없다.
- [ ] `mkdocs/docs/handover/index.md`의 원본 현황·대응표가 `manifest.json`과 일치한다.
- [ ] `nav`에 모든 문서가 등록되었고, 홈(`mkdocs/docs/index.md`)의 요약 표와 최근 업데이트를 가이드 3.4절대로 갱신했다.
- [ ] 빌드 검증이 가이드 6절의 기준대로 통과했다(`nav` 누락과 깨진 앵커도 이 단계에서 잡힙니다).
- [ ] 원본 폴더의 파일은 하나도 바뀌지 않았다.
