"""Phase 5 workflow safety and Phase 6 Windows release readiness tests."""

from __future__ import annotations

import json
import struct
import tomllib
from pathlib import Path

from vegas_doc.core.resource_manager import ResourceManager
from vegas_doc.core.single_instance import SingleInstanceGuard
from vegas_doc.version import BUILD_INFO, __version__


ROOT = Path(__file__).resolve().parents[1]


def test_package_version_has_one_python_source() -> None:
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))

    assert pyproject["project"]["dynamic"] == ["version"]
    assert pyproject["tool"]["setuptools"]["dynamic"]["version"]["attr"] == "vegas_doc.version.__version__"
    assert BUILD_INFO.version == __version__ == "0.1.0"


def test_windows_version_info_is_generated_from_package_version(tmp_path: Path) -> None:
    from scripts.generate_version_info import write_version_info

    target = write_version_info(tmp_path / "version_info.txt")
    text = target.read_text(encoding="utf-8")

    assert "Vegas Inc." in text
    assert BUILD_INFO.version in text
    assert "Vegas_Total_Solution_Doc.exe" in text


def test_release_metadata_contains_real_hashes_without_secrets(tmp_path: Path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    from scripts import generate_release_metadata as metadata

    executable = tmp_path / "dist" / "Vegas_Total_Solution_Doc" / "Vegas_Total_Solution_Doc.exe"
    installer = tmp_path / "dist" / "installer" / "Vegas_Total_Solution_Doc_Setup.exe"
    executable.parent.mkdir(parents=True)
    installer.parent.mkdir(parents=True)
    executable.write_bytes(b"exe")
    installer.write_bytes(b"installer")
    monkeypatch.setattr(metadata, "ROOT", tmp_path)

    checksums, manifest_path = metadata.generate_release_metadata(installer.parent)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert executable.name in checksums.read_text(encoding="ascii")
    assert installer.name in checksums.read_text(encoding="ascii")
    assert manifest["version"] == BUILD_INFO.version
    serialized = json.dumps(manifest).lower()
    assert "secret_key" not in serialized and "x-ocr-secret" not in serialized


def test_application_icon_contains_required_resolutions() -> None:
    payload = (ROOT / "assets" / "app.ico").read_bytes()
    _reserved, image_type, count = struct.unpack_from("<HHH", payload)
    sizes: set[int] = set()
    for index in range(count):
        width, height = struct.unpack_from("BB", payload, 6 + index * 16)
        assert width == height
        sizes.add(width or 256)

    assert image_type == 1
    assert {16, 32, 48, 64, 128, 256}.issubset(sizes)


def test_resource_manager_resolves_source_branding() -> None:
    icon = ResourceManager.for_package().branding_path("app.ico")
    wordmark = ResourceManager.for_package().branding_path("vegas_logo.png")

    assert icon is not None and icon.resolve() == (ROOT / "assets" / "app.ico").resolve()
    assert wordmark is not None and wordmark.resolve() == (ROOT / "assets" / "vegas_logo.png").resolve()


def test_single_instance_guard_rejects_second_owner(tmp_path: Path, qapp) -> None:  # type: ignore[no-untyped-def]
    test_mutex = f"VegasTotalSolutionDoc.Test.{tmp_path.name}"
    first = SingleInstanceGuard(tmp_path, mutex_name=test_mutex)
    second = SingleInstanceGuard(tmp_path, mutex_name=test_mutex)
    try:
        assert first.acquire()
        assert not second.acquire(timeout_ms=0)
    finally:
        first.release()
        second.release()


def test_installer_and_workflow_static_release_contract() -> None:
    installer = (ROOT / "installer" / "Vegas_Total_Solution_Doc.iss").read_text(encoding="utf-8")
    workflow = (ROOT / ".github" / "workflows" / "build-windows-installer.yml").read_text(encoding="utf-8")
    spec = (ROOT / "Vegas_Total_Solution_Doc.spec").read_text(encoding="utf-8")

    assert "DefaultDirName={autopf}\\Vegas Inc\\Vegas Total Solution Doc" in installer
    assert "SetupIconFile=..\\assets\\app.ico" in installer
    assert "desktopicon" in installer and "CloseApplications=yes" in installer
    assert "Vegas-Total-Solution-Doc-Installer" in workflow
    assert "Vegas_Total_Solution_Doc_Setup.exe" in workflow
    assert "100 MB" in workflow and "160 MB" in workflow
    assert not any(ord(character) < 9 for character in workflow)
    assert 'icon="assets/app.ico"' in spec
    assert '"assets/vegas_logo.png"' in spec
    assert 'version="build/version_info.txt"' in spec
