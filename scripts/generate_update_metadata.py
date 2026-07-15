"""Generate checksums and a manifest for the cumulative lightweight updater."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from vegas_doc.version import BUILD_INFO  # noqa: E402

UPDATE_FILENAME = "Vegas_Total_Solution_Doc_Update.exe"
MINIMUM_BASE_VERSION = "0.1.0"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _git_commit(root: Path) -> str:
    configured_commit = os.getenv("VEGAS_GIT_COMMIT") or os.getenv("GITHUB_SHA")
    if configured_commit:
        return configured_commit
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=root,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def _payload_files(root: Path) -> list[dict[str, object]]:
    distribution = root / "dist" / "Vegas_Total_Solution_Doc"
    candidates = [distribution / "Vegas_Total_Solution_Doc.exe"]
    pyside_directory = distribution / "_internal" / "PySide6"
    candidates.extend(
        pyside_directory / filename
        for filename in ("QtPrintSupport.pyd", "Qt6PrintSupport.dll")
    )
    resources = distribution / "_internal" / "vegas_doc" / "resources"
    if resources.is_dir():
        candidates.extend(path for path in resources.rglob("*") if path.is_file())
    return [
        {
            "path": path.relative_to(distribution).as_posix(),
            "bytes": path.stat().st_size,
            "sha256": _sha256(path),
        }
        for path in candidates
        if path.is_file()
    ]


def write_update_metadata(root: Path = ROOT) -> tuple[Path, Path, Path]:
    """Write the updater checksum, machine-readable manifest, and user guide."""

    output_directory = root / "dist" / "update"
    updater = output_directory / UPDATE_FILENAME
    if not updater.is_file():
        raise FileNotFoundError(f"Lightweight updater not found: {updater}")

    output_directory.mkdir(parents=True, exist_ok=True)
    checksum = _sha256(updater)
    checksums_path = output_directory / "checksums.txt"
    checksums_path.write_text(f"{checksum}  {updater.name}\n", encoding="utf-8")

    manifest_path = output_directory / "update_manifest.json"
    manifest = {
        "product": BUILD_INFO.product,
        "version": BUILD_INFO.version,
        "package_type": "cumulative-lightweight-update",
        "cumulative": True,
        "requires_full_install": True,
        "minimum_base_version": MINIMUM_BASE_VERSION,
        "includes_updates_through": BUILD_INFO.version,
        "build_date_utc": datetime.now(timezone.utc).isoformat(),
        "git_commit": _git_commit(root),
        "updater": {
            "name": updater.name,
            "bytes": updater.stat().st_size,
            "sha256": checksum,
        },
        "payload": _payload_files(root),
    }
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    guide_path = output_directory / "README_UPDATE.txt"
    guide_path.write_text(
        "Vegas Total Solution Doc 누적 소형 업데이트\n"
        f"버전: {BUILD_INFO.version}\n\n"
        "1. Vegas Total Solution Doc를 종료합니다.\n"
        f"2. {UPDATE_FILENAME}를 실행합니다.\n"
        "3. 기존 전체 설치본을 자동으로 찾아 최신 EXE와 리소스를 교체합니다.\n\n"
        "이 파일은 신규 설치용이 아닙니다. 기본 프로그램이 없으면 전체 설치파일을 먼저 설치하세요.\n"
        "소형 업데이트는 누적형이므로 이전 소형 업데이트를 따로 설치할 필요가 없습니다.\n",
        encoding="utf-8",
    )
    return checksums_path, manifest_path, guide_path


if __name__ == "__main__":
    for generated in write_update_metadata():
        print(generated)
