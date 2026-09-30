# 인수인계 업무노트

전임자에게 받은 인수인계 자료(한글, 엑셀, 파워포인트, PDF 등)를 폴더에 넣으면, AI 에이전트가 모든 파일을 읽어 마크다운으로 변환하고 검색 가능한 문서 사이트(MkDocs)로 정리해 주는 프로젝트입니다.

```mermaid
flowchart LR
    A["1. RAW<br>(받은 인수인계 자료를 그대로 넣음)"] --> B["변환 스크립트<br>(kordoc · OfficeCLI)"]
    B --> C["2. 변환 중간본<br>(파일별 마크다운 · 보고서)"]
    C --> D["AI 에이전트<br>(주제별 정리 · 사이트 등록)"]
    D --> E["mkdocs/docs/handover<br>(문서 사이트)"]
```

---

## 목차

- [폴더 구성](#폴더-구성)
- [1. 처음 설치하기 (설치 스크립트)](#1-처음-설치하기-설치-스크립트)
- [2. 수동 설치 (설치 스크립트가 실패했을 때)](#2-수동-설치-설치-스크립트가-실패했을-때)
- [3. 설치 확인](#3-설치-확인)
- [4. 사용 방법](#4-사용-방법)
- [5. 문제 해결](#5-문제-해결)
- [6. 주의 사항](#6-주의-사항)
- [7. 다른 PC에 전달하기](#7-다른-pc에-전달하기)

---

## 폴더 구성

| 경로 | 설명 |
| :--- | :--- |
| `1. RAW/` | 인수인계 자료 원본입니다. 받은 자료를 폴더째 그대로 넣는 곳입니다. 하위 폴더가 복잡하거나 파일이 많아도 됩니다. Git에 올라가지 않습니다. |
| `2. 변환 중간본/` | 변환 스크립트가 만드는 파일별 마크다운, `manifest.json`(진행 기록), `변환 보고서.md`입니다. Git에 올라가지 않습니다. |
| `mkdocs/docs/handover/` | AI 에이전트가 주제별로 정리한 문서입니다. 사이트에 표시됩니다. |
| `mkdocs/mkdocs.yml` | 사이트 설정과 메뉴(`nav`)입니다. |
| `setup/` | Windows·macOS 설치 스크립트입니다. |
| `.agents/skills/` | AI 에이전트가 따르는 작업 절차(스킬)입니다. |
| `AGENTS.md`, `CLAUDE.md` | AI 에이전트에게 주는 프로젝트 지침입니다. |

**지원하는 파일 형식**

| 형식 | 읽는 도구 |
| :--- | :--- |
| 한글(`.hwp`, `.hwpx`), PDF, 워드(`.docx`), 엑셀(`.xlsx`, `.xls`), 이미지(`.png`, `.jpg`) | [kordoc](https://github.com/chrisryugj/kordoc) |
| 파워포인트(`.pptx`) | [OfficeCLI](https://github.com/iOfficeAI/OfficeCLI) |
| 텍스트(`.txt`, `.md`), CSV | 변환 스크립트 |

`.doc`, `.ppt` 같은 옛 형식과 압축 파일(`.zip` 등)은 변환하지 않고 보고서에 조치 방법을 알려 줍니다. 각각 `.docx`, `.pptx`로 다시 저장하거나 압축을 풀어서 넣으면 됩니다.

---

## 1. 처음 설치하기 (설치 스크립트)

Python조차 없는, **아무 프로그램도 설치되지 않은 PC**를 기준으로 설명합니다. 문서 사이트를 보려면 Python과 Material for MkDocs가, 자료를 변환하려면 Node.js·kordoc·OfficeCLI가 필요하며, 설치 스크립트가 이를 모두 설치합니다. 설치 스크립트가 필요한 프로그램이 있는지 확인하고, **없는 것만 설치**합니다. 이미 설치된 프로그램은 건너뛰므로 여러 번 실행해도 안전합니다. 처음 설치에는 인터넷 속도에 따라 10~30분이 걸립니다.

**설치되는 프로그램**

| 프로그램 | 용도 | 버전 |
| :--- | :--- | :--- |
| Git | 변경 기록 관리 | 최신 |
| Python | 문서 사이트(MkDocs)와 변환 스크립트 실행. 쓸 수 있는 Python이 없으면 [uv](https://docs.astral.sh/uv/)로 사용자 폴더에 내려받으므로 관리자 권한이 필요 없습니다. | 3.10 이상 (새로 받으면 3.12) |
| Node.js | kordoc 실행 | 20 이상 (LTS) |
| kordoc | 한글·PDF·워드·엑셀·이미지 읽기 | 최신 |
| OfficeCLI | 파워포인트 읽기, 워드·엑셀 보조 | 최신 |
| MkDocs | 문서 사이트 생성기 (프로젝트 안의 `.venv`에 설치) | `mkdocs/requirements.txt` 기준 |
| Material for MkDocs | 사이트 테마와 확장 문법(`mkdocs-material`). **없으면 사이트가 열리지 않습니다.** (`.venv`에 설치) | `mkdocs/requirements.txt` 기준 |
| 다이어그램 미리보기 도구 | AI 에이전트가 Mermaid 도표를 미리 확인 (`.agents/skills/pretty-mermaid`에 설치, 실패해도 변환에는 영향 없음) | `package.json` 기준 |
| Homebrew | macOS 프로그램 설치 도구 (macOS만) | 최신 |

AI 코딩 에이전트는 설치 스크립트가 설치하지 않습니다. [1.4절](#14-ai-코딩-에이전트-설치)을 참고해 따로 설치합니다.

### 1.1 프로젝트 폴더 받기

새 PC에는 Git이 없으므로 **압축 파일(ZIP)로 받는 방법**을 권장합니다.

1. 저장소 페이지에서 `Code` → `Download ZIP`을 누르거나, 전달받은 압축 파일을 준비합니다.
2. 압축을 풉니다. 위치는 **경로가 짧은 곳**이 좋습니다.
    - Windows: `C:\work\인수인계` 처럼 드라이브 바로 아래 (바탕화면이나 `다운로드` 폴더 안쪽은 경로가 길어집니다)
    - macOS: `문서` 폴더 아래 등 원하는 곳
3. **Windows만**: 압축을 풀기 전에 ZIP 파일을 오른쪽 클릭 → `속성` → 아래쪽의 `차단 해제`를 체크하고 `확인`을 누릅니다. 인터넷에서 받은 파일이라는 표시가 지워져, 설치 스크립트를 실행할 때 보안 경고가 덜 뜹니다.

Git이 이미 있다면 `git clone <저장소 주소>`로 받아도 됩니다.

### 1.2 Windows

1. 파일 탐색기에서 프로젝트 폴더 안의 `setup` 폴더를 엽니다.
2. **`setup-windows.cmd`를 더블클릭**합니다.
3. 진행 중에 다음 창이 뜰 수 있습니다.
    - `Windows의 PC 보호` (SmartScreen): `추가 정보` → `실행`을 누릅니다.
    - `사용자 계정 컨트롤` (이 앱이 디바이스를 변경할 수 있도록 허용하시겠어요?): `예`를 누릅니다. Git, Node.js를 설치할 때마다 뜰 수 있습니다.
4. `설치가 끝났습니다.`가 나오면 Enter를 눌러 창을 닫습니다.
5. **열려 있는 PowerShell·터미널·VS Code 창을 모두 닫았다가 다시 엽니다.** 새로 설치한 프로그램의 경로는 새 창에서만 반영됩니다.

설치 스크립트가 하는 일은 다음과 같습니다.

| 단계 | 내용 |
| :--- | :--- |
| 1 | `winget`(Windows 기본 패키지 관리자)이 있는지 확인. 없으면 Microsoft Store의 `앱 설치 관리자` 페이지를 엽니다. |
| 2 | Git, Node.js LTS가 없으면 `winget`으로 설치 |
| 3 | 현재 사용자의 PowerShell 스크립트 실행 허용(`RemoteSigned`) |
| 4 | kordoc 설치 (`npm install -g kordoc`) |
| 5 | OfficeCLI 설치 (공식 설치 스크립트) |
| 6 | Git 긴 경로 허용. Windows 긴 경로가 꺼져 있으면 안내 메시지 표시 |
| 7 | `serve-windows.ps1 -Prepare`로 Python을 준비하고(없으면 uv로 내려받음) 가상환경(`.venv`)에 MkDocs, Material for MkDocs 설치. 기존 `.venv`가 깨져 있으면 다시 만듭니다. 이어서 다이어그램 도구 설치 |
| 8 | 설치 확인 (`convert.py --check`) |

더블클릭이 안 되면 프로젝트 폴더에서 PowerShell을 열고 다음을 실행합니다. 이렇게 실행하면 끝에 Enter 입력을 기다리지 않습니다(AI 에이전트도 이 명령을 씁니다). 탐색기 주소창에 `powershell`을 입력하고 Enter를 누르면 그 폴더에서 PowerShell이 열립니다.

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File setup\setup-windows.ps1
```

**긴 경로 허용 (권장)**: 6단계에서 `Windows 긴 경로가 허용되어 있지 않습니다`라는 주의가 나오면, 시작 메뉴에서 PowerShell을 오른쪽 클릭 → `관리자 권한으로 실행`한 창에서 다음을 실행하고 PC를 다시 시작합니다. 인수인계 자료는 폴더가 깊고 파일명이 길어서 경로 길이 제한(260자)에 걸리기 쉽습니다.

```powershell
New-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" -Name "LongPathsEnabled" -Value 1 -PropertyType DWORD -Force
```

### 1.3 macOS

1. `응용 프로그램` → `유틸리티` → `터미널`을 엽니다.
2. `cd `(cd 다음에 공백 한 칸)를 입력한 뒤, Finder에서 **프로젝트 폴더를 터미널 창으로 끌어다 놓고** Enter를 누릅니다. 폴더 경로가 자동으로 입력됩니다.
3. 다음을 입력하고 Enter를 누릅니다.

    ```bash
    bash setup/setup-mac.sh
    ```

4. 진행 중에 다음을 요구할 수 있습니다.
    - `Password:`: Mac 로그인 암호를 입력하고 Enter를 누릅니다. **입력하는 글자는 화면에 보이지 않습니다.**
    - `Xcode Command Line Tools` 설치 창: `설치`를 누르고 끝날 때까지 기다립니다.
5. `설치가 끝났습니다.`가 나오면 **터미널을 닫았다가 다시 엽니다.**

설치 스크립트가 하는 일은 다음과 같습니다.

| 단계 | 내용 |
| :--- | :--- |
| 1 | Homebrew가 없으면 설치하고, 새 터미널에서도 쓸 수 있게 `~/.zprofile`에 등록 |
| 2 | Git, Node.js 20 이상이 없으면 `brew`로 설치 |
| 3 | kordoc 설치 (`npm install -g kordoc`) |
| 4 | OfficeCLI 설치 (공식 설치 스크립트, `~/.local/bin`에 설치되고 `~/.zshrc`에 경로 등록) |
| 5 | `serve-mac.sh --prepare`로 Python을 준비하고(없으면 uv로 내려받음) 가상환경(`.venv`)에 MkDocs와 Material for MkDocs 설치. 기존 `.venv`가 깨져 있으면 다시 만듭니다. |
| 6 | 다이어그램 미리보기 도구 설치 |
| 7 | 설치 확인 (`convert.py --check`) |

### 1.4 AI 코딩 에이전트 설치

변환된 결과를 주제별로 정리하고 사이트에 등록하는 작업은 AI 코딩 에이전트가 합니다. 이 프로젝트의 지침은 `AGENTS.md`에 있고, Claude Code는 `CLAUDE.md`를 통해 같은 지침을 읽습니다.

에이전트는 설치 스크립트가 설치하지 않으므로 **사용자가 직접 한 번 설치**해야 합니다. 에이전트를 설치한 뒤에는 설치 스크립트를 따로 실행하지 않아도 됩니다. 에이전트에게 `업무노트 실행해줘`라고 요청하면 문서 사이트에 필요한 프로그램(Python, MkDocs, Material for MkDocs)을 에이전트가 설치합니다. 자료 변환을 요청하면 변환 도구도 에이전트가 설치합니다.

Claude Code를 예로 들면 다음 순서로 진행합니다. 설치 명령은 바뀔 수 있으므로 [공식 설치 안내](https://docs.anthropic.com/claude-code)를 함께 확인하십시오.

1. 터미널을 엽니다.
    - Windows: 시작 메뉴에서 `PowerShell`을 검색해 엽니다.
    - macOS: `⌘ + Space`를 누르고 `터미널`을 입력해 엽니다.
2. 설치 명령을 붙여 넣고 Enter를 누릅니다.

    ```powershell
    # Windows (PowerShell)
    irm https://claude.ai/install.ps1 | iex
    ```

    ```bash
    # macOS (터미널)
    curl -fsSL https://claude.ai/install.sh | bash
    ```

3. 설치 중에 Git for Windows(Git Bash)가 필요하다는 안내가 나오면, `winget install -e --id Git.Git`로 설치한 뒤 PowerShell을 새로 열고 2번을 다시 실행합니다(Windows만).
4. 터미널을 새로 열고 프로젝트 폴더로 이동한 뒤 `claude`를 실행합니다. 처음 실행하면 브라우저가 열리며 로그인을 요청합니다.
    - Windows: `cd C:\work\인수인계`
    - macOS: `cd `를 입력한 뒤 Finder에서 프로젝트 폴더를 터미널 창으로 끌어다 놓고 Enter
5. `업무노트 실행해줘`라고 입력합니다. 사람이 해야 하는 단계가 있으면 에이전트가 안내하고 기다립니다([4.5절](#45-ai가-대신할-수-없는-단계)).

---

## 2. 수동 설치 (설치 스크립트가 실패했을 때)

설치 스크립트가 중간에 실패하면, 실패한 단계부터 아래 명령을 직접 실행합니다. 각 단계가 끝나면 **터미널(PowerShell) 창을 새로 열고** 다음 단계로 넘어갑니다.

### 2.1 Windows (PowerShell)

```powershell
# ① 스크립트 실행 허용 (확인 질문에는 Y)
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned

# ② Git, Python, Node.js
winget install -e --id Git.Git --accept-source-agreements --accept-package-agreements
winget install -e --id Python.Python.3.12 --accept-source-agreements --accept-package-agreements
winget install -e --id OpenJS.NodeJS.LTS --accept-source-agreements --accept-package-agreements
```

`winget`을 쓸 수 없다면 공식 사이트에서 설치 파일을 받습니다: [Git](https://git-scm.com/download/win), [Python](https://www.python.org/downloads/) (설치 첫 화면에서 **Add python.exe to PATH** 체크), [Node.js](https://nodejs.org/) (LTS).

창을 새로 연 뒤 이어서 실행합니다.

```powershell
# ③ kordoc (OCR 엔진 설치 스크립트 허용 옵션 포함)
npm install -g kordoc --allow-scripts=onnxruntime-node,protobufjs

# ④ OfficeCLI
irm https://raw.githubusercontent.com/iOfficeAI/OfficeCLI/main/install.ps1 | iex

# ⑤ Git 긴 경로 허용
git config --global core.longpaths true
```

창을 새로 열고 **프로젝트 폴더로 이동한 뒤** 실행합니다.

```powershell
# ⑥ 파이썬 가상환경과 MkDocs · Material for MkDocs
py -m venv .venv
.venv\Scripts\python -m pip install -r mkdocs\requirements.txt

# ⑦ 다이어그램 미리보기 도구 (선택)
cd .agents\skills\pretty-mermaid; npm install; cd ..\..\..
```

### 2.2 macOS (터미널)

```bash
# ① Homebrew (끝나면 화면 마지막 'Next steps'의 명령 두 줄을 그대로 실행)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# ② Git, Python, Node.js
brew install git python node

# ③ kordoc (OCR 엔진 설치 스크립트 허용 옵션 포함)
npm install -g kordoc --allow-scripts=onnxruntime-node,protobufjs

# ④ OfficeCLI (또는 brew install officecli)
curl -fsSL https://raw.githubusercontent.com/iOfficeAI/OfficeCLI/main/install.sh | bash
```

터미널을 새로 열고 **프로젝트 폴더로 이동한 뒤** 실행합니다.

```bash
# ⑤ 파이썬 가상환경과 MkDocs · Material for MkDocs
python3 -m venv .venv
.venv/bin/pip install -r mkdocs/requirements.txt

# ⑥ 다이어그램 미리보기 도구 (선택)
(cd .agents/skills/pretty-mermaid && npm install)
```

원문 설치 안내는 각 프로젝트 저장소에 있습니다: [kordoc](https://github.com/chrisryugj/kordoc), [OfficeCLI](https://github.com/iOfficeAI/OfficeCLI).

---

## 3. 설치 확인

설치 스크립트는 마지막에 자동으로 확인합니다. 따로 확인하려면 프로젝트 폴더에서 다음을 실행합니다.

```powershell
# Windows
.venv\Scripts\python .agents\skills\handover-to-mkdocs\scripts\convert.py --check
```

```bash
# macOS
.venv/bin/python .agents/skills/handover-to-mkdocs/scripts/convert.py --check
```

여섯 줄 모두 버전이 나오면 준비가 끝난 것입니다. 위의 세 줄은 문서 사이트, 아래의 세 줄은 자료 변환에 필요한 도구입니다.

```text
python           3.12.x
mkdocs           1.6.1
mkdocs-material  9.x.x
node             v22.x.x
kordoc           4.x.x
officecli        1.x.x
```

`.venv`가 아직 없으면 `python`, `mkdocs`, `mkdocs-material`이 `없음`으로 나옵니다. 파이썬이 아예 없어서 이 명령을 실행할 수 없는 PC라면 확인을 건너뛰고 설치 스크립트를 실행합니다. `없음`이 나오면 창을 새로 연 뒤 다시 확인하고, 그래도 `없음`이면 설치 스크립트를 한 번 더 실행하거나 [2. 수동 설치](#2-수동-설치-설치-스크립트가-실패했을-때)에서 해당 단계를 진행합니다.

---

## 4. 사용 방법

### 4.1 원본 자료 넣기

받은 자료를 `1. RAW/` 폴더에 **폴더째 그대로** 복사합니다. 파일명을 바꾸거나 정리할 필요는 없습니다.

- 압축 파일(`.zip` 등)은 압축을 풀어서 넣고, 압축 파일 자체는 넣지 않습니다.
- 암호가 걸린 문서는 암호를 풀어 다시 저장한 뒤 넣습니다.
- `.doc`, `.ppt` 같은 옛 형식은 `.docx`, `.pptx`로 다시 저장한 파일만 넣습니다. 옛 형식 파일을 함께 두면 매번 미지원 형식으로 보고됩니다.

### 4.2 AI 에이전트에게 맡기기 (권장)

프로젝트 폴더에서 AI 에이전트(예: `claude`)를 실행하고 다음처럼 요청합니다.

```text
1. RAW 폴더의 자료를 모두 변환해서 사이트에 등록해줘.
```

에이전트는 `handover-to-mkdocs` 스킬에 따라 다음 순서로 작업합니다.

1. 도구 설치 여부를 확인합니다.
2. 변환 스크립트로 모든 파일을 중간본으로 변환하고, 실패하거나 변환할 수 없는 파일을 보고합니다.
3. 자료를 업무 주제별로 묶는 분류안을 보여 줍니다.
4. 주제별로 문서를 만들어 사이트 메뉴에 등록합니다.
5. `mkdocs/docs/handover/index.md`에 전체 현황과 원본 파일 대응표를 만듭니다.

파일이 많으면 시간이 걸립니다. 중간에 끊겨도 같은 요청을 다시 하면 `manifest.json`의 기록을 보고 이어서 진행합니다.

### 4.3 변환만 직접 실행하기

에이전트 없이 변환 결과만 보고 싶을 때 사용합니다.

```powershell
# Windows
.venv\Scripts\python .agents\skills\handover-to-mkdocs\scripts\convert.py --dry-run   # 대상 파일과 처리 도구만 확인
.venv\Scripts\python .agents\skills\handover-to-mkdocs\scripts\convert.py             # 변환 실행
```

```bash
# macOS
.venv/bin/python .agents/skills/handover-to-mkdocs/scripts/convert.py --dry-run
.venv/bin/python .agents/skills/handover-to-mkdocs/scripts/convert.py
```

결과는 `2. 변환 중간본/`에 생기고, `변환 보고서.md`에서 상태별 현황과 조치가 필요한 파일을 확인할 수 있습니다.

| 옵션 | 설명 |
| :--- | :--- |
| `--check` | 필요한 도구의 설치 여부만 확인 |
| `--dry-run` | 변환하지 않고 대상 목록만 출력 |
| `--force` | 이미 변환한 파일도 모두 다시 변환 |
| `--ocr` | 모든 PDF·이미지에 글자 인식(OCR) 사용. 스캔 PDF는 이 옵션 없이도 자동으로 OCR을 시도 |
| `--timeout 초` | 파일 하나의 변환 제한 시간 (기본 600초) |

### 4.4 사이트 보기

AI 에이전트에게 `업무노트 실행해줘`라고 요청하는 방법이 가장 쉽습니다. 에이전트가 사이트 실행 스크립트를 실행해, Python·MkDocs·Material for MkDocs가 없으면 **관리자 권한 없이 자동으로 설치**하고 사이트를 띄운 뒤 주소를 알려 줍니다. 전체 설치 스크립트를 미리 실행하지 않은 PC에서도 됩니다.

직접 실행하려면 프로젝트 폴더에서 다음을 실행합니다. 필요한 프로그램이 없으면 먼저 설치한 뒤 사이트를 띄웁니다.

```powershell
# Windows
powershell -NoProfile -ExecutionPolicy Bypass -File setup\serve-windows.ps1
```

```bash
# macOS
bash setup/serve-mac.sh
```

브라우저에서 <http://127.0.0.1:8000>을 엽니다. 종료하려면 터미널에서 `Ctrl + C`를 누릅니다. 이미 실행 중이면 새로 띄우지 않고 주소만 알려 줍니다.

### 4.5 AI가 대신할 수 없는 단계

설치·실행 스크립트는 AI 에이전트가 대신할 수 없는 일을 만나면 `[사용자 조치 필요]`로 시작하는 안내를 보여 주고 멈춥니다. 안내대로 진행한 뒤 에이전트에게 **"했어"**라고 말하면, 에이전트가 같은 스크립트를 다시 실행해 멈춘 지점부터 이어서 진행합니다.

| 상황 | 사용자가 할 일 |
| :--- | :--- |
| macOS에 Homebrew가 없음 (자료 변환 도구 설치 때) | 안내된 명령을 터미널에 붙여 넣고 Mac 로그인 암호 입력 |
| macOS 계정이 관리자가 아님 | 관리자 계정으로 로그인하거나 IT 담당자에게 요청 |
| Windows에 winget이 없음 | Microsoft Store에서 `앱 설치 관리자` 설치 |
| Windows에서 Git·Node.js 설치 승인이 안 됨 | 다시 뜨는 `사용자 계정 컨트롤` 창에서 `예` 누르기, 또는 IT 담당자에게 설치 요청 |
| 인터넷에 연결할 수 없음 | 인터넷 연결 확인, 회사망이면 보안 프로그램·프록시 확인 |

문서 사이트만 볼 때는 위 상황 가운데 인터넷 연결 문제만 해당합니다.

### 4.6 자료가 추가·수정되었을 때

새 파일을 원본 폴더에 넣거나 기존 파일을 바꾼 뒤 에이전트에게 요청합니다.

```text
원본 폴더에 자료가 추가됐어. 사이트에 반영해줘.
```

변환 스크립트는 바뀌지 않은 파일을 건너뛰고, 새 파일과 바뀐 파일만 다시 변환합니다. 원본에서 지운 파일은 사이트에서도 정리됩니다.

---

## 5. 문제 해결

| 증상 | 해결 방법 |
| :--- | :--- |
| `setup-windows.cmd`를 더블클릭하면 창이 바로 닫힌다 | 프로젝트 폴더에서 PowerShell을 열고 [1.2절](#12-windows)의 `powershell -NoProfile -ExecutionPolicy Bypass -File setup\setup-windows.ps1` 명령으로 실행하면 오류 메시지를 볼 수 있습니다. |
| `winget을 찾을 수 없습니다` | Microsoft Store에서 `앱 설치 관리자(App Installer)`를 설치·업데이트한 뒤 다시 실행합니다. Store를 쓸 수 없는 회사 PC라면 [2.1절](#21-windows-powershell)의 공식 설치 파일 링크를 이용합니다. |
| 회사 PC라 관리자 권한(사용자 계정 컨트롤 `예`)이 없다 | Git, Node.js 설치에 관리자 권한이 필요할 수 있습니다. 문서 사이트(Python, MkDocs)는 관리자 권한 없이 설치됩니다. 사내 IT 담당자에게 두 프로그램 설치를 요청한 뒤 설치 스크립트를 다시 실행하면 나머지는 사용자 권한으로 설치됩니다. |
| `'py'`, `'python3'`, `'node'`, `'npm'`을 찾을 수 없다 | 설치 후 터미널을 새로 열지 않은 경우가 대부분입니다. 창을 닫고 다시 엽니다. Windows에서 Python을 설치 파일로 설치했다면 `Add python.exe to PATH`를 체크했는지 확인합니다. |
| PowerShell에서 `npm.ps1 ... PSSecurityException` 또는 `이 시스템에서 스크립트를 실행할 수 없으므로` | [2.1절](#21-windows-powershell) ①의 `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`를 실행하고 PowerShell을 다시 엽니다. |
| kordoc 실행 시 `MODULE_NOT_FOUND` 또는 `Cannot find module ...\dist\cli.js` | 설치가 깨진 상태입니다. `npm uninstall -g kordoc` 후 `npm install -g kordoc --allow-scripts=onnxruntime-node,protobufjs`를 다시 실행합니다. |
| kordoc 설치 때 `npm warn install-scripts ... onnxruntime-node` 경고가 나오고 스캔 PDF·이미지를 읽지 못한다 | npm 12부터 설치 스크립트가 기본으로 막혀 OCR 엔진이 설치되지 않은 상태입니다. 위 명령처럼 `--allow-scripts` 옵션을 붙여 다시 설치합니다. |
| macOS에서 `npm install -g` 중 `EACCES: permission denied` | Node.js를 공식 설치 파일(.pkg)로 설치한 경우입니다. `brew install node`로 다시 설치하고 터미널을 새로 연 뒤 설치 스크립트를 다시 실행합니다. |
| macOS에서 `officecli`를 실행하면 `확인되지 않은 개발자` 경고가 뜬다 | 브라우저로 직접 내려받은 경우입니다. `xattr -d com.apple.quarantine ~/.local/bin/officecli`를 실행하거나 설치 스크립트로 다시 설치합니다. |
| `--check`에서 `officecli 없음` | 설치 후 터미널을 새로 엽니다. 그래도 안 되면 [OfficeCLI Releases](https://github.com/iOfficeAI/OfficeCLI/releases)에서 운영체제에 맞는 파일을 받아 실행하면 PATH에 자동 설치됩니다. |
| 보고서에 `ENCRYPTED`, `DRM_PROTECTED` | 암호나 문서보안이 걸린 파일입니다. 해제한 사본을 원래 파일과 바꿔 넣고 다시 변환합니다. 원래 파일을 남겨 두면 계속 실패로 보고됩니다. |
| 보고서에 `IMAGE_BASED_PDF` | 스캔 PDF를 OCR로도 읽지 못한 경우입니다. 첫 OCR 때 약 18MB의 모델을 내려받으므로 인터넷 연결을 확인하고 다시 실행합니다. |
| Windows에서 `경로가 너무 깁니다` 또는 파일을 찾지 못함 | [1.2절](#12-windows)의 **긴 경로 허용**을 진행하거나, 프로젝트 폴더를 `C:\work`처럼 짧은 경로로 옮깁니다. |
| `mkdocs serve`·`mkdocs build`에서 `Unrecognised theme name: 'material'`, 또는 `.venv\Scripts\mkdocs`(`.venv/bin/mkdocs`)를 찾을 수 없다 | Material for MkDocs가 설치되지 않았거나 `.venv`가 깨진 상태입니다. 설치 스크립트를 다시 실행하면 `.venv`를 점검해 필요하면 다시 만들고 Material for MkDocs를 설치합니다. |
| `mkdocs serve`에서 `Address already in use` | 이미 실행 중인 사이트가 있습니다. 기존 터미널에서 `Ctrl + C`로 종료하거나 `-a 127.0.0.1:8001`을 붙여 다른 포트를 씁니다. |
| 사내망(폐쇄망)이라 설치가 안 된다 | kordoc의 [오프라인 배포 안내](https://github.com/chrisryugj/kordoc/blob/main/docs/offline-deployment.md)와 OfficeCLI Releases의 단일 실행 파일을 이용합니다. |

---

## 6. 주의 사항

- **원본은 변환 과정에서 바뀌지 않습니다.** 스크립트와 에이전트는 원본 폴더의 파일을 읽기만 합니다.
- **개인정보**: 이 사이트는 본인만 로컬에서 보는 용도이므로, 담당자 연락처 등 원문의 개인정보를 가리지 않고 그대로 옮깁니다. 사이트나 저장소를 다른 사람과 공유할 일이 생기면 먼저 내용을 확인하십시오.
- **Git**: 원본(`1. RAW/`)과 중간본(`2. 변환 중간본/`)은 `.gitignore`로 제외되어 저장소에 올라가지 않습니다. 정리된 문서(`mkdocs/docs/`)에는 원문 내용이 그대로 들어 있으므로 저장소를 공개하지 마십시오.

---

## 7. 다른 PC에 전달하기

이 프로젝트 폴더를 다른 사람이나 새 PC에 전달할 때는 다음 파일을 **빼고** 압축합니다. 받는 PC에서 다시 만들어지거나, 개인정보가 들어 있는 파일입니다.

| 뺄 파일 | 이유 |
| :--- | :--- |
| `.venv/`, `.agents/skills/pretty-mermaid/node_modules/` | 보내는 PC의 운영체제 전용 파일입니다. 받는 PC에서 자동으로 다시 설치됩니다. |
| `mkdocs/site/` | 빌드 결과물입니다. |
| `1. RAW/` 안의 자료, `2. 변환 중간본/` | 인수인계 원본과 변환 결과입니다. 개인정보가 들어 있습니다. |

Git을 쓴다면 **변경 사항을 모두 커밋한 뒤** 다음 명령으로 압축 파일을 만듭니다. 위의 파일은 `.gitignore`로 제외되어 있으므로 자동으로 빠집니다. 커밋하지 않은 변경 사항은 들어가지 않습니다.

```bash
git archive --format=zip -o 업무노트.zip HEAD
```

`mkdocs/docs/`의 정리된 문서에는 원문 내용이 그대로 들어 있습니다. 받는 사람이 보면 안 되는 내용이 있다면 전달하기 전에 확인하십시오.

받는 사람은 다음 순서로 진행합니다.

1. [1.1절](#11-프로젝트-폴더-받기)처럼 압축을 풉니다. Windows는 `C:\work\인수인계`처럼 경로가 짧은 곳을 권장합니다.
2. [1.4절](#14-ai-코딩-에이전트-설치)대로 AI 에이전트를 설치합니다.
3. 프로젝트 폴더에서 에이전트를 실행하고 `업무노트 실행해줘`라고 요청합니다.
