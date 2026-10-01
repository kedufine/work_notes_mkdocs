"""서드파티 라이선스 전문을 빌드 결과물에 포함한다.

`mkdocs build`/`serve`는 Material for MkDocs의 JS·CSS·템플릿 복사본을 사이트에 넣는다.
MIT 라이선스는 모든 복사본에 저작권 표기와 라이선스 전문을 포함하도록 요구하므로,
저장소의 `LICENSES/` 원문을 사이트의 `licenses/` 아래로 복사한다.
푸터 링크는 `overrides/partials/copyright.html`에 있다.
"""

import logging
import shutil
from importlib import metadata
from pathlib import Path

# "mkdocs." 아래 로거의 WARNING은 `--strict` 빌드를 실패시킨다.
log = logging.getLogger("mkdocs.hooks.licenses")

# (저장소 원문 파일, 사이트 안 경로, 원문을 대조할 설치 패키지, 패키지 안 라이선스 경로)
LICENSES = [
    (
        "LICENSES/mkdocs-material.txt",
        "licenses/mkdocs-material/LICENSE.txt",
        "mkdocs-material",
        "licenses/LICENSE",
    ),
]


def _normalize(text: str) -> str:
    # Windows에서 Git이 줄바꿈을 CRLF로 바꿔도 같은 원문으로 본다.
    return text.replace("\r\n", "\n").strip()


def _installed_license(dist_name: str, license_path: str) -> str | None:
    try:
        return metadata.distribution(dist_name).read_text(license_path)
    except metadata.PackageNotFoundError:
        return None


def on_post_build(config, **kwargs):
    repo_root = Path(config.config_file_path).resolve().parent.parent
    site_dir = Path(config.site_dir)

    for source, target, dist_name, license_path in LICENSES:
        source_path = repo_root / source
        if not source_path.is_file():
            log.warning("라이선스 원문이 없습니다: %s", source)
            continue

        # 설치된 패키지의 원문과 다르면(업그레이드로 저작권 연도가 바뀐 경우 등) 알린다.
        installed = _installed_license(dist_name, license_path)
        if installed is None:
            log.warning("%s 패키지에서 %s를 찾지 못했습니다.", dist_name, license_path)
        elif _normalize(installed) != _normalize(source_path.read_text(encoding="utf-8")):
            log.warning(
                "%s이(가) 설치된 %s %s의 라이선스와 다릅니다. 패키지의 %s로 교체하세요.",
                source,
                dist_name,
                metadata.version(dist_name),
                license_path,
            )

        target_path = site_dir / target
        target_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source_path, target_path)
