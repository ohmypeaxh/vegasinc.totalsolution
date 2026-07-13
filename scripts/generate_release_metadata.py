"""Generate release checksums and a secret-free build manifest."""

from __future__ import annotations

import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from vegas_doc.version import BUILD_INFO  # noqa: E402


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _git_commit() -> str:
    configured = os.getenv("GITHUB_SHA") or os.getenv("VEGAS_GIT_COMMIT")
    if configured:
        return configured
    git = shutil.which("git")
    if git is None and sys.platform == "win32":
        candidate = Path(os.environ.get("ProgramFiles", r"C:\Program Files")) / "Git" / "cmd" / "git.exe"
        git = str(candidate) if candidate.is_file() else None
    if git is None:
        return "unknown"
    try:
        return subprocess.check_output(
            [git, "rev-parse", "HEAD"], cwd=ROOT, text=True, stderr=subprocess.DEVNULL
        ).strip()
    except (OSError, subprocess.SubprocessError):
        return "unknown"


def generate_release_metadata(output_directory: Path) -> tuple[Path, Path]:
    """Create checksums.txt and build_manifest.json for verified release files."""

    executable = ROOT / "dist" / "Vegas_Total_Solution_Doc" / "Vegas_Total_Solution_Doc.exe"
    installer = ROOT / "dist" / "installer" / "Vegas_Total_Solution_Doc_Setup.exe"
    missing = [str(path) for path in (executable, installer) if not path.is_file()]
    if missing:
        raise FileNotFoundError("Missing release files: " + ", ".join(missing))
    output_directory.mkdir(parents=True, exist_ok=True)
    hashes = {executable.name: _sha256(executable), installer.name: _sha256(installer)}
    checksums = output_directory / "checksums.txt"
    checksums.write_text("".join(f"{digest}  {name}\n" for name, digest in hashes.items()), encoding="ascii")
    manifest = output_directory / "build_manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "product": BUILD_INFO.product,
                "version": BUILD_INFO.version,
                "build_date_utc": datetime.now(timezone.utc).isoformat(),
                "git_commit": _git_commit(),
                "python_version": platform.python_version(),
                "pyinstaller_version": _package_version("PyInstaller"),
                "executable": executable.name,
                "installer": installer.name,
                "sha256": hashes,
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    return checksums, manifest


def _package_version(name: str) -> str:
    from importlib.metadata import PackageNotFoundError, version

    try:
        return version(name)
    except PackageNotFoundError:
        return "unknown"


if __name__ == "__main__":
    checksum_path, manifest_path = generate_release_metadata(ROOT / "dist" / "installer")
    print(checksum_path)
    print(manifest_path)
