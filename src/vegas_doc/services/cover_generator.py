"""Excel cover placeholder replacement and two-page PDF generation."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

import fitz

from vegas_doc.core.resource_manager import ResourceManager
from vegas_doc.models.cover_document import (
    LOGO_PLACEHOLDERS,
    REQUIRED_COVER_SHEETS,
    TEXT_PLACEHOLDERS,
    CoverDocumentRequest,
)


@dataclass(frozen=True, slots=True)
class LogoPlacement:
    """One logo placeholder and its fixed aspect-preserving dimension."""

    token: str
    dimension: str
    centimetres: float


LOGO_PLACEMENTS = (
    LogoPlacement("##고객사로고1##", "height", 2.11),
    LogoPlacement("##고객사로고2##", "width", 1.38),
    LogoPlacement("##고객사로고3##", "width", 2.4),
    LogoPlacement("##고객사로고4##", "width", 2.4),
    LogoPlacement("##고객사로고5##", "width", 2.4),
)


class CoverWorkbookRenderer(Protocol):
    """Boundary for Excel template rendering implementations."""

    def render(self, request: CoverDocumentRequest, temporary_directory: Path) -> tuple[Path, ...]:
        """Render the configured sheets to ordered one-page PDF files."""


class ExcelPowerShellCoverRenderer:
    """Render the workbook through installed Microsoft Excel without Python COM packages."""

    def __init__(self, script_path: Path | None = None, timeout_seconds: int = 180) -> None:
        self._script_path = script_path or ResourceManager.for_package().path("scripts", "render_cover.ps1")
        self._timeout_seconds = timeout_seconds

    def render(self, request: CoverDocumentRequest, temporary_directory: Path) -> tuple[Path, ...]:
        """Invoke the bundled PowerShell/Excel automation script with JSON data."""

        if os.name != "nt":
            raise RuntimeError("Cover Generator는 Microsoft Excel이 설치된 Windows에서만 사용할 수 있습니다.")
        if not self._script_path.is_file():
            raise RuntimeError(f"Cover Generator Excel 스크립트를 찾을 수 없습니다: {self._script_path}")
        powershell = Path(os.environ.get("SystemRoot", r"C:\Windows")) / "System32" / "WindowsPowerShell" / "v1.0" / "powershell.exe"
        if not powershell.is_file():
            raise RuntimeError("Windows PowerShell을 찾을 수 없습니다.")

        exports = tuple(temporary_directory / f"cover-sheet-{index}.pdf" for index in range(1, 3))
        payload = {
            "template_path": str(request.template_path.resolve()),
            "logo_path": str(request.customer_logo_path.resolve()),
            "replacements": request.replacements(),
            "required_tokens": [*TEXT_PLACEHOLDERS, *LOGO_PLACEHOLDERS],
            "logo_placements": [
                {"token": item.token, "dimension": item.dimension, "centimetres": item.centimetres}
                for item in LOGO_PLACEMENTS
            ],
            "sheet_exports": [
                {"sheet_name": sheet_name, "output_path": str(output_path.resolve())}
                for sheet_name, output_path in zip(REQUIRED_COVER_SHEETS, exports, strict=True)
            ],
        }
        request_path = temporary_directory / "cover-request.json"
        request_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        command = [
            str(powershell),
            "-NoProfile",
            "-NonInteractive",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(self._script_path),
            "-RequestPath",
            str(request_path),
        ]
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=self._timeout_seconds,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                check=False,
            )
        except subprocess.TimeoutExpired as error:
            raise TimeoutError("Excel PDF 변환 시간이 초과되었습니다. Excel 대화상자가 열려 있는지 확인해 주세요.") from error
        if result.returncode != 0:
            details = (result.stderr or result.stdout).strip()
            raise RuntimeError(details or "Excel PDF 변환에 실패했습니다. Microsoft Excel 설치 상태를 확인해 주세요.")
        missing = tuple(path for path in exports if not path.is_file())
        if missing:
            raise RuntimeError("Excel이 필수 PDF 페이지를 생성하지 못했습니다: " + ", ".join(path.name for path in missing))
        return exports


class CoverPdfGenerator:
    """Validate, render, merge, and atomically save a two-page cover PDF."""

    def __init__(self, renderer: CoverWorkbookRenderer | None = None) -> None:
        self._renderer = renderer or ExcelPowerShellCoverRenderer()

    def generate(self, request: CoverDocumentRequest) -> Path:
        """Create one PDF containing the cover sheet followed by the label sheet."""

        errors = request.validation_errors()
        if errors:
            raise ValueError("\n".join(errors))
        output_path = _available_output_path(request.output_directory / request.output_filename())
        temporary_directory = Path(tempfile.mkdtemp(prefix="vegas_cover_", dir=request.output_directory))
        temporary_output = temporary_directory / output_path.name
        try:
            sheet_pdfs = self._renderer.render(request, temporary_directory)
            if len(sheet_pdfs) != 2:
                raise RuntimeError("개별표지와 개별라벨 PDF가 각각 한 장씩 생성되어야 합니다.")
            merged = fitz.open()
            try:
                for sheet_name, pdf_path in zip(REQUIRED_COVER_SHEETS, sheet_pdfs, strict=True):
                    with fitz.open(pdf_path) as source:
                        if source.page_count != 1:
                            raise RuntimeError(f"'{sheet_name}' 시트가 {source.page_count}페이지로 출력되었습니다. 한 페이지 인쇄영역을 확인해 주세요.")
                        merged.insert_pdf(source)
                if merged.page_count != 2:
                    raise RuntimeError("Cover PDF는 정확히 2페이지여야 합니다.")
                merged.save(temporary_output)
            finally:
                merged.close()
            temporary_output.replace(output_path)
        finally:
            shutil.rmtree(temporary_directory, ignore_errors=True)
        return output_path


def _available_output_path(path: Path) -> Path:
    if not path.exists():
        return path
    index = 2
    while True:
        candidate = path.with_stem(f"{path.stem}_{index}")
        if not candidate.exists():
            return candidate
        index += 1
