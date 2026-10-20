# 서드파티 소프트웨어 고지

이 프로젝트가 사용하는 오픈소스 소프트웨어와 각 라이선스를 정리한 목록입니다. 프로젝트 자체의 라이선스는 저장소 루트의 [`LICENSE`](../LICENSE)(MIT)입니다.

- 라이선스와 버전은 2026-10-12에 각 패키지의 메타데이터와 공식 저장소에서 확인한 값입니다. 이후 버전에서 바뀔 수 있으므로, 정확한 조건은 각 저장소의 라이선스 원문을 확인하십시오.
- 라이선스 전문을 이 저장소에 두는 대상은 **복사본이 저장소나 빌드된 사이트에 포함되는 소프트웨어**(1절)입니다. 2절과 3절의 소프트웨어는 저장소에 포함되어 있지 않고, 설치하거나 사이트를 열 때 각 배포처에서 내려받습니다.

## 1. 저장소와 빌드된 사이트에 포함되는 소프트웨어

| 소프트웨어 | 포함된 위치 | 라이선스 | 라이선스 전문 |
| :--- | :--- | :--- | :--- |
| [Material for MkDocs](https://github.com/squidfunk/mkdocs-material) | `mkdocs/overrides/partials/copyright.html`(원본 템플릿의 수정본), 빌드된 사이트의 JS·CSS·템플릿 | MIT | [`mkdocs-material.txt`](mkdocs-material.txt) |
| [Pretty Mermaid Skills](https://github.com/imxv/Pretty-mermaid-skills) | `.agents/skills/pretty-mermaid/` | MIT | [`.agents/skills/pretty-mermaid/LICENSE`](../.agents/skills/pretty-mermaid/LICENSE) |

`mkdocs-material.txt`는 빌드할 때 `mkdocs/hooks/licenses.py`가 사이트의 `licenses/` 아래로 복사하며, 사이트 하단의 `MIT License` 링크가 이 파일을 가리킵니다.

## 2. 설치할 때 내려받는 소프트웨어

설치 스크립트(`setup/`)나 수동 설치 절차가 각 공식 배포처에서 내려받아 설치합니다.

### 2.1 문서 사이트 (Python 패키지)

| 소프트웨어 | 용도 | 라이선스 |
| :--- | :--- | :--- |
| [MkDocs](https://github.com/mkdocs/mkdocs) | 문서 사이트 생성기 | BSD-2-Clause |
| [Material for MkDocs](https://github.com/squidfunk/mkdocs-material) | 사이트 테마 | MIT |
| [mkdocs-charts-plugin](https://github.com/timvink/mkdocs-charts-plugin) | Vega-Lite 코드 블록 처리 | MIT |
| [PyMdown Extensions](https://github.com/facelessuser/pymdown-extensions) | 마크다운 확장(Material의 의존 패키지) | MIT |
| [Python-Markdown](https://github.com/Python-Markdown/markdown) | 마크다운 변환(MkDocs의 의존 패키지) | BSD-3-Clause |
| [Pygments](https://github.com/pygments/pygments) | 코드 강조(Material의 의존 패키지) | BSD-2-Clause |

### 2.2 문서 변환과 다이어그램 도구

| 소프트웨어 | 용도 | 라이선스 |
| :--- | :--- | :--- |
| [kordoc](https://github.com/chrisryugj/kordoc) | 한글·PDF·워드·엑셀·이미지 변환 | MIT |
| [OfficeCLI](https://github.com/iOfficeAI/OfficeCLI) | 파워포인트 변환 | Apache-2.0 |
| [beautiful-mermaid](https://github.com/lukilabs/beautiful-mermaid) | Mermaid 다이어그램 렌더링(Pretty Mermaid 스킬의 의존 패키지) | MIT |
| [resvg-js](https://github.com/thx/resvg-js) | SVG를 PNG로 변환(Pretty Mermaid 스킬의 의존 패키지) | MPL-2.0 |

### 2.3 실행 환경

| 소프트웨어 | 용도 | 라이선스 |
| :--- | :--- | :--- |
| [Python](https://www.python.org/) | 문서 사이트와 변환 스크립트 실행 | PSF-2.0 |
| [Git](https://git-scm.com/) | 프로젝트 내려받기와 버전 관리 | GPL-2.0 |
| [Node.js](https://nodejs.org/) | kordoc과 다이어그램 도구 실행 | MIT |
| [uv](https://github.com/astral-sh/uv) | Python이 없을 때 Python 내려받기 | Apache-2.0 또는 MIT |
| [Homebrew](https://brew.sh) | macOS 패키지 관리자 | BSD-2-Clause |

## 3. 사이트를 열 때 CDN에서 불러오는 소프트웨어

사이트 화면이 브라우저에서 CDN(jsDelivr, unpkg)을 통해 직접 불러옵니다. 저장소와 빌드된 사이트에는 복사본이 없습니다.

| 소프트웨어 | 버전 | 용도 | 라이선스 |
| :--- | :--- | :--- | :--- |
| [beautiful-mermaid](https://github.com/lukilabs/beautiful-mermaid) | 1.1.3 | Mermaid 다이어그램 렌더링 | MIT |
| [Mermaid](https://github.com/mermaid-js/mermaid) | 11.17.2 | beautiful-mermaid가 지원하지 않는 다이어그램 유형의 렌더링 | MIT |
| [Vega](https://github.com/vega/vega) | 5.33.1 | 차트 렌더링 | BSD-3-Clause |
| [Vega-Lite](https://github.com/vega/vega-lite) | 5.23.0 | 차트 문법 | BSD-3-Clause |
| [Vega-Embed](https://github.com/vega/vega-embed) | 6.29.0 | 차트를 문서에 삽입 | BSD-3-Clause |
| [Pretendard](https://github.com/orioncactus/pretendard) | 1.3.9 | 사이트 글꼴 | OFL-1.1 |

## 4. 목록을 갱신해야 하는 경우

- **의존성을 추가하거나 버전을 올린 경우**: 해당 절의 표에 반영합니다. Material for MkDocs를 올렸을 때 `mkdocs-material.txt`가 설치된 패키지의 라이선스와 달라지면 `mkdocs build --strict`가 실패하므로, 패키지의 `licenses/LICENSE`로 교체합니다.
- **CDN 대신 파일을 직접 포함하도록 바꾼 경우**: 폐쇄망 등의 이유로 3절의 스크립트나 글꼴 파일을 저장소 또는 사이트에 직접 넣으면 복사본을 배포하는 것이 됩니다. 이때는 해당 소프트웨어를 1절로 옮기고, 라이선스 전문을 이 폴더에 추가합니다.
