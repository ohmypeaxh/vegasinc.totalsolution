"""Lightweight cumulative update packaging tests."""

from __future__ import annotations

from pathlib import Path

from vegas_doc.version import BUILD_INFO

ROOT = Path(__file__).resolve().parents[1]


def test_lightweight_update_replaces_only_cumulative_runtime_files() -> None:
    script = (ROOT / "installer" / "Vegas_Total_Solution_Doc_Update.iss").read_text(encoding="utf-8")

    assert BUILD_INFO.version == "0.1.1"
    assert "Vegas_Total_Solution_Doc.exe" in script
    assert "_internal\\vegas_doc\\resources\\*" in script
    assert 'Source: "..\\dist\\Vegas_Total_Solution_Doc\\*"' not in script
    assert "Uninstallable=no" in script
    assert "CreateUninstallRegKey=no" in script
    assert "FindBaseInstallDir" in script
    assert "기본 설치본을 찾지 못했습니다" in script


def test_update_workflow_uploads_versioned_executable_artifact() -> None:
    workflow = (ROOT / ".github" / "workflows" / "build-windows-update.yml").read_text(encoding="utf-8")

    assert "workflow_dispatch:" in workflow
    assert "windows-latest" in workflow
    assert 'python-version: "3.12"' in workflow
    assert "python -m pytest -q" in workflow
    assert "Vegas_Total_Solution_Doc_Update.exe" in workflow
    assert "Vegas-Total-Solution-Doc-Update-0.1.1" in workflow
    assert "actions/upload-artifact@v4" in workflow
    assert "Updater exceeds the 30 MB hard limit" in workflow


def test_update_build_script_generates_manifest_and_checksum() -> None:
    build_script = (ROOT / "scripts" / "build_update.bat").read_text(encoding="utf-8")
    metadata_script = (ROOT / "scripts" / "generate_update_metadata.py").read_text(encoding="utf-8")

    assert "Vegas_Total_Solution_Doc_Update.iss" in build_script
    assert "generate_update_metadata.py" in build_script
    assert '"cumulative": True' in metadata_script
    assert '"requires_full_install": True' in metadata_script
    assert '"minimum_base_version": MINIMUM_BASE_VERSION' in metadata_script
