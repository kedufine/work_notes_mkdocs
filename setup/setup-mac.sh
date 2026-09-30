#!/bin/bash
# 인수인계 업무노트 macOS 설치 스크립트
# 사용법: 프로젝트 폴더에서 `bash setup/setup-mac.sh`
# 이미 설치된 프로그램은 건너뛰므로 여러 번 실행해도 안전하다.
#
# 종료 코드: 0 성공, 1 실패, 3 사용자 조치 필요
#   3이면 '[사용자 조치 필요]' 안내를 출력한다(Mac 암호 입력처럼 AI 에이전트가 대신할 수 없는 일).
#   사용자가 조치를 마치면 이 스크립트를 다시 실행해 이어서 진행한다.

set -u
cd "$(dirname "$0")/.." || exit 1
ROOT="$(pwd)"
KORDOC_SCRIPTS="onnxruntime-node,protobufjs"

step() { printf '\n\033[1;36m[%s] %s\033[0m\n' "$1" "$2"; }
ok()   { printf '  \033[32m완료\033[0m %s\n' "$1"; }
warn() { printf '  \033[33m주의\033[0m %s\n' "$1"; }
fail() { printf '  \033[31m실패\033[0m %s\n' "$1"; exit 1; }
has()  { command -v "$1" >/dev/null 2>&1; }

# AI 에이전트가 대신할 수 없는 일을 안내하고 종료 코드 3으로 끝낸다
need_user() {
    printf '\n\033[1;33m[사용자 조치 필요] %s\033[0m\n' "$1"
    shift
    local line
    for line in "$@"; do printf '  %s\n' "$line"; done
    printf '  → 끝나면 AI에게 "했어"라고 말하십시오. 이어서 진행합니다. (직접 실행했다면 이 스크립트를 다시 실행하십시오.)\n'
    exit 3
}

node_ok()   { node -e 'process.exit(+process.versions.node.split(".")[0] >= 20 ? 0 : 1)' >/dev/null 2>&1; }

echo "인수인계 업무노트 설치를 시작합니다. 프로젝트 폴더: $ROOT"

# ---------------------------------------------------------------------------
step 1/7 "Homebrew"
# 이미 설치되어 있지만 PATH에 없는 경우(Apple Silicon)를 먼저 확인한다
if ! has brew; then
    for b in /opt/homebrew/bin/brew /usr/local/bin/brew; do
        [ -x "$b" ] && eval "$("$b" shellenv)"
    done
fi
if ! has brew; then
    # Homebrew는 관리자 계정의 암호 입력이 필요하다
    if ! id -Gn | tr ' ' '\n' | grep -qx admin; then
        need_user "관리자 계정 필요" \
            "지금 Mac 사용자 계정은 관리자가 아니어서 Homebrew를 설치할 수 없습니다." \
            "관리자 계정으로 로그인해 이 프로젝트를 다시 열거나, IT 담당자에게 Homebrew 설치를 요청하십시오."
    fi
    # AI 에이전트가 실행한 경우(입력 창이 없음)에는 암호를 입력할 수 없으므로 사용자에게 맡긴다
    if [ ! -t 0 ] && ! sudo -n true 2>/dev/null; then
        need_user "Homebrew 설치 (Mac 암호 입력 필요)" \
            "1. ⌘ + Space를 누르고 '터미널'을 입력한 뒤 Enter를 눌러 터미널을 엽니다." \
            "2. 아래 명령을 복사해 터미널에 붙여 넣고 Enter를 누릅니다." \
            "   /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\"" \
            "3. 'Password:'가 나오면 Mac 로그인 암호를 입력하고 Enter를 누릅니다. 입력한 글자는 화면에 보이지 않습니다." \
            "4. 'Press RETURN'이 나오면 Enter를 누릅니다. 'Xcode Command Line Tools' 설치 창이 뜨면 '설치'를 누릅니다." \
            "5. 'Installation successful!'이 나오면 터미널 창을 닫습니다."
    fi
    echo "  Homebrew를 설치합니다. Mac 로그인 암호를 물으면 입력하십시오(입력한 글자는 화면에 보이지 않습니다)."
    echo "  Xcode Command Line Tools 설치 창이 뜨면 '설치'를 누르십시오. 수 분이 걸릴 수 있습니다."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)" \
        || fail "Homebrew 설치에 실패했습니다. https://brew.sh 안내를 확인하십시오."
    for b in /opt/homebrew/bin/brew /usr/local/bin/brew; do
        [ -x "$b" ] && eval "$("$b" shellenv)"
    done
    has brew || fail "Homebrew를 찾을 수 없습니다. 터미널을 새로 열고 다시 실행하십시오."
fi
# 새 터미널에서도 brew를 찾도록 ~/.zprofile에 등록한다(Apple Silicon 기본 경로는 PATH에 없음)
BREW_BIN="$(command -v brew)"
if [ "$BREW_BIN" = "/opt/homebrew/bin/brew" ] && ! grep -qs "brew shellenv" "$HOME/.zprofile"; then
    echo "eval \"\$($BREW_BIN shellenv)\"" >> "$HOME/.zprofile"
fi
ok "$(brew --version | head -1)"

# ---------------------------------------------------------------------------
step 2/7 "Git · Node.js"
if git --version >/dev/null 2>&1; then
    ok "$(git --version)"
else
    brew install git || fail "Git 설치에 실패했습니다."
    ok "$(git --version)"
fi

if has node && node_ok; then
    ok "Node.js $(node --version)"
else
    brew install node || fail "Node.js 설치에 실패했습니다."
    hash -r
    node_ok || fail "Node.js 20 이상을 찾을 수 없습니다. 다른 경로의 오래된 Node.js가 먼저 잡히는지 확인하십시오(which node)."
    ok "Node.js $(node --version)"
fi

# ---------------------------------------------------------------------------
step 3/7 "kordoc (한글·PDF·워드·엑셀·이미지 읽기)"
if has kordoc; then
    ok "kordoc $(kordoc --version) (이미 설치됨)"
else
    # npm 12부터 설치 스크립트가 기본 차단되므로 OCR 엔진(onnxruntime-node)의 스크립트를 허용한다
    if ! npm install -g kordoc --allow-scripts="$KORDOC_SCRIPTS"; then
        warn "권한 오류(EACCES)라면 Node.js를 공식 설치 파일로 설치한 경우입니다. 'brew install node'로 다시 설치한 뒤 이 스크립트를 다시 실행하십시오."
        fail "kordoc 설치에 실패했습니다."
    fi
    hash -r
    ok "kordoc $(kordoc --version)"
fi

# ---------------------------------------------------------------------------
step 4/7 "OfficeCLI (파워포인트 읽기)"
export PATH="$HOME/.local/bin:$PATH"
if has officecli; then
    ok "officecli $(OFFICECLI_SKIP_UPDATE=1 officecli --version) (이미 설치됨)"
else
    # 공식 설치 스크립트는 ~/.local/bin에 설치하고 ~/.zshrc에 PATH를 추가한다
    curl -fsSL https://raw.githubusercontent.com/iOfficeAI/OfficeCLI/main/install.sh | bash \
        || fail "OfficeCLI 설치에 실패했습니다. https://github.com/iOfficeAI/OfficeCLI 안내를 확인하십시오."
    hash -r
    has officecli || fail "officecli를 찾을 수 없습니다. 터미널을 새로 열고 다시 실행하십시오."
    ok "officecli $(OFFICECLI_SKIP_UPDATE=1 officecli --version)"
fi

# ---------------------------------------------------------------------------
step 5/7 "Python 가상환경과 MkDocs · Material for MkDocs"
# 사이트 실행 스크립트가 Python 준비(없으면 uv로 내려받기)·.venv 점검·Material 설치를 맡는다
bash setup/serve-mac.sh --prepare
code=$?
[ "$code" = 3 ] && exit 3
[ "$code" = 0 ] || fail "사이트 도구를 준비하지 못했습니다. 위의 메시지를 확인하십시오."

# ---------------------------------------------------------------------------
step 6/7 "다이어그램 미리보기 도구 (pretty-mermaid)"
if [ -d .agents/skills/pretty-mermaid/node_modules ]; then
    ok "이미 설치됨"
else
    (cd .agents/skills/pretty-mermaid && npm install --silent) && ok "설치됨" \
        || warn "설치하지 못했습니다. 변환 작업에는 영향이 없습니다."
fi

# ---------------------------------------------------------------------------
step 7/7 "설치 확인"
if .venv/bin/python .agents/skills/handover-to-mkdocs/scripts/convert.py --check; then
    printf '\n\033[1;32m설치가 끝났습니다.\033[0m\n'
    echo "다음 순서로 사용하십시오."
    echo "  1. 터미널을 닫고 새로 엽니다(설치한 프로그램의 경로를 반영하기 위해)."
    echo "  2. 받은 자료를 '1. RAW' 폴더에 넣습니다."
    echo "  3. 프로젝트 폴더에서 AI 에이전트를 실행하고 '자료를 모두 변환해서 사이트에 등록해줘'라고 요청합니다."
    echo "  4. 사이트 보기: AI 에이전트에게 '업무노트 실행해줘'라고 요청하거나 bash setup/serve-mac.sh → http://127.0.0.1:8000"
else
    fail "확인에 실패한 도구가 있습니다. 터미널을 새로 열고 이 스크립트를 한 번 더 실행하십시오."
fi
