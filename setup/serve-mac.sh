#!/bin/bash
# 업무노트 사이트 실행 스크립트 (macOS)
# 사용법: 프로젝트 폴더에서 `bash setup/serve-mac.sh`
#   --prepare  사이트 실행에 필요한 것만 준비하고 끝낸다(서버는 띄우지 않음).
# 사이트에 필요한 Python·MkDocs·Material for MkDocs가 없으면 자동으로 설치한다.
# 암호 입력이나 확인 창 없이 끝나도록 관리자 권한이 필요 없는 방법만 쓴다.
#   - 쓸 수 있는 Python 3.10 이상이 없으면 uv(사용자 폴더 ~/.local/bin에 설치)로 Python을 내려받는다.
# 변환 도구(kordoc·OfficeCLI)는 사이트 실행에 필요 없으므로 설치하지 않는다(setup-mac.sh 담당).
#
# 종료 코드: 0 성공, 1 실패, 3 사용자 조치 필요
#   3이면 '[사용자 조치 필요]' 안내를 출력한다. 사용자가 조치를 마치면 이 스크립트를 다시 실행해 이어서 진행한다.

set -u
cd "$(dirname "$0")/.." || exit 1
ROOT="$(pwd)"
HOST="127.0.0.1"
PORT="8000"
URL="http://$HOST:$PORT"
VENV_PY=".venv/bin/python"
PREPARE_ONLY=0
[ "${1:-}" = "--prepare" ] && PREPARE_ONLY=1

info() { printf '\033[1;36m%s\033[0m\n' "$1"; }
ok()   { printf '  \033[32m완료\033[0m %s\n' "$1"; }
warn() { printf '  \033[33m주의\033[0m %s\n' "$1"; }
fail() { printf '  \033[31m실패\033[0m %s\n' "$1"; exit 1; }

# AI 에이전트가 대신할 수 없는 일을 안내하고 종료 코드 3으로 끝낸다
# 사용법: need_user "제목" "1. 할 일" "2. 할 일" ...
need_user() {
    printf '\n\033[1;33m[사용자 조치 필요] %s\033[0m\n' "$1"
    shift
    local line
    for line in "$@"; do printf '  %s\n' "$line"; done
    printf '  → 끝나면 AI에게 "했어"라고 말하십시오. 이어서 진행합니다. (직접 실행했다면 이 스크립트를 다시 실행하십시오.)\n'
    exit 3
}

# 내려받기가 실패했을 때, 인터넷 연결 문제면 사용자 조치로, 아니면 실패로 끝낸다
net_or_fail() {
    if ! curl -fsI --max-time 10 https://pypi.org/simple/ >/dev/null 2>&1; then
        need_user "인터넷 연결 확인" \
            "1. Wi-Fi나 유선 인터넷이 연결되어 있는지 확인하십시오." \
            "2. 회사망이라면 보안 프로그램이나 프록시가 pypi.org, astral.sh, github.com 접속을 막고 있지 않은지 IT 담당자에게 확인하십시오."
    fi
    fail "$1"
}

python_ok() { "$1" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)' >/dev/null 2>&1; }
site_ok()   { "$VENV_PY" -c 'import mkdocs, material' >/dev/null 2>&1; }

# 설치 없이 쓸 수 있는 Python 3.10 이상을 찾는다
find_python() {
    local cands=(/opt/homebrew/bin/python3 /usr/local/bin/python3)
    # /usr/bin/python3는 Command Line Tools가 없으면 설치 창을 띄우므로, 있을 때만 후보에 넣는다
    if xcode-select -p >/dev/null 2>&1; then cands+=(/usr/bin/python3); fi
    local c
    for c in "${cands[@]}"; do
        if [ -x "$c" ] && python_ok "$c"; then echo "$c"; return 0; fi
    done
    return 1
}

# uv를 찾고, 없으면 사용자 폴더에 설치한다(관리자 권한 불필요)
find_or_install_uv() {
    local c
    for c in "$(command -v uv 2>/dev/null)" "$HOME/.local/bin/uv" "$HOME/.cargo/bin/uv"; do
        if [ -n "$c" ] && [ -x "$c" ]; then echo "$c"; return 0; fi
    done
    echo "  Python을 받기 위해 uv를 사용자 폴더에 설치합니다." >&2
    curl -LsSf https://astral.sh/uv/install.sh | env UV_NO_MODIFY_PATH=1 sh >&2 || return 1
    [ -x "$HOME/.local/bin/uv" ] && echo "$HOME/.local/bin/uv"
}

make_venv() {
    rm -rf .venv
    local py uv
    if py="$(find_python)"; then
        echo "  $py 로 가상환경(.venv)을 만듭니다."
        "$py" -m venv .venv && return 0
        warn "가상환경을 만들지 못해 uv로 다시 시도합니다."
        rm -rf .venv
    else
        echo "  사용할 수 있는 Python이 없어 새로 내려받습니다."
    fi
    uv="$(find_or_install_uv)" || net_or_fail "uv를 설치하지 못했습니다."
    # --seed: pip를 함께 넣어 기존 설치 스크립트(setup-mac.sh)와 같은 방식으로 쓸 수 있게 한다
    "$uv" venv --python 3.12 --seed .venv || net_or_fail "Python을 내려받지 못했습니다."
}

# ---------------------------------------------------------------------------
info "업무노트 사이트를 준비합니다. 프로젝트 폴더: $ROOT"

if site_ok; then
    ok "MkDocs · Material for MkDocs 준비됨"
else
    # 가상환경이 없거나, 만든 Python이 사라져 깨졌으면 다시 만든다
    if ! "$VENV_PY" -c 'import sys' >/dev/null 2>&1; then
        [ -e .venv ] && warn "기존 가상환경(.venv)이 동작하지 않아 다시 만듭니다."
        make_venv
    fi
    echo "  MkDocs와 Material for MkDocs를 설치합니다."
    "$VENV_PY" -m pip install -q --disable-pip-version-check -r mkdocs/requirements.txt \
        || net_or_fail "MkDocs 설치에 실패했습니다. 위의 오류 메시지를 확인하십시오."
    site_ok || fail "Material for MkDocs를 불러오지 못했습니다."
    ok "MkDocs · Material for MkDocs 설치됨"
fi
ok "$(.venv/bin/mkdocs --version | cut -d' ' -f1-3), Material for MkDocs $("$VENV_PY" -c 'import importlib.metadata as m; print(m.version("mkdocs-material"))')"

[ "$PREPARE_ONLY" = 1 ] && { info "준비가 끝났습니다."; exit 0; }

# 이미 사이트가 떠 있으면 새로 띄우지 않는다
if "$VENV_PY" -c "import socket,sys; s=socket.socket(); s.settimeout(1); sys.exit(0 if s.connect_ex(('$HOST',$PORT))==0 else 1)"; then
    info "이미 $PORT 포트에서 실행 중입니다. 브라우저에서 $URL 을 여십시오."
    exit 0
fi

info "사이트를 실행합니다: $URL (종료: Ctrl + C)"
exec .venv/bin/mkdocs serve -a "$HOST:$PORT" -f mkdocs/mkdocs.yml
