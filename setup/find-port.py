"""업무노트 사이트를 띄울 포트를 고른다(serve-mac.sh, serve-windows.ps1이 사용).

8000번부터 8010번까지 차례로 확인해 한 줄을 출력한다.
- running <포트>: 그 포트에서 이미 업무노트 사이트가 실행 중이다.
- free <포트>: 비어 있는 포트다. 이 포트로 사이트를 띄우면 된다.
- none: 모든 포트를 다른 프로그램이 쓰고 있다.

포트가 열려 있기만 하면 다른 프로그램일 수 있으므로, 응답한 페이지가 업무노트인지 확인한다.
표준 라이브러리만 사용한다.
"""

import socket
import sys
import urllib.request

FIRST_PORT = 8000
LAST_PORT = 8010
# 업무노트의 모든 페이지가 불러오는 스크립트 경로. site_name은 사용자가 바꿀 수 있으므로 쓰지 않는다
SITE_MARKER = "javascripts/pretty-mermaid.js"


def is_busy(host: str, port: int) -> bool:
    with socket.socket() as s:
        s.settimeout(1)
        return s.connect_ex((host, port)) == 0


def is_work_notes(host: str, port: int) -> bool:
    try:
        with urllib.request.urlopen(f"http://{host}:{port}/", timeout=3) as res:
            body = res.read(500_000).decode("utf-8", "replace")
    except Exception:
        return False
    return SITE_MARKER in body


def main() -> int:
    host = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
    for port in range(FIRST_PORT, LAST_PORT + 1):
        if not is_busy(host, port):
            print("free", port)
            return 0
        if is_work_notes(host, port):
            print("running", port)
            return 0
    print("none")
    return 0


if __name__ == "__main__":
    sys.exit(main())
