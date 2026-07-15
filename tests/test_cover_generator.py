"""Cover Generator mappings, PDF composition, and UI tests."""

from __future__ import annotations

from pathlib import Path

import fitz
import pytest
from PySide6.QtGui import QPageSize
from PySide6.QtPrintSupport import QPrinter
from PySide6.QtWidgets import QDialog, QLabel

from vegas_doc.models.cover_document import (
    LOGO_PLACEHOLDERS,
    QUALIFICATION_TITLES,
    TEXT_PLACEHOLDERS,
    CoverDocumentRequest,
)
from vegas_doc.services.cover_generator import LOGO_PLACEMENTS, CoverPdfGenerator
from vegas_doc.services.cover_printer import CoverPdfPrinter


ROOT = Path(__file__).resolve().parents[1]


class FakeCoverRenderer:
    """Create deterministic single-page PDFs without requiring Microsoft Excel."""

    def __init__(self, page_counts: tuple[int, int] = (1, 1)) -> None:
        self.page_counts = page_counts
        self.request: CoverDocumentRequest | None = None

    def render(self, request: CoverDocumentRequest, temporary_directory: Path) -> tuple[Path, ...]:
        self.request = request
        outputs: list[Path] = []
        for index, page_count in enumerate(self.page_counts, start=1):
            output = temporary_directory / f"sheet-{index}.pdf"
            document = fitz.open()
            for _ in range(page_count):
                document.new_page(width=595, height=842)
            document.save(output)
            document.close()
            outputs.append(output)
        return tuple(outputs)


def _request(tmp_path: Path, abbreviation: str = "IQ") -> CoverDocumentRequest:
    template = tmp_path / "cover-template.xlsx"
    template.write_bytes(b"test workbook")
    logo = tmp_path / "customer-logo.png"
    logo.write_bytes(b"test image")
    return CoverDocumentRequest(
        template,
        logo,
        tmp_path,
        "Pass Box",
        abbreviation,
        "VP-IQ-PB-001",
        "VR-IQ-PB-001",
        "2026",
    )


def test_cover_request_replaces_all_text_placeholders_and_builds_filename(tmp_path: Path) -> None:
    request = _request(tmp_path, "IOQ")

    replacements = request.replacements()

    assert tuple(replacements) == TEXT_PLACEHOLDERS
    assert replacements == {
        "##장비명##": "Pass Box",
        "##적격성평가축약##": "IOQ",
        "##적격성평가한글##": "설치 및 운전적격성평가",
        "##적격성평가영문##": "Installation & Operational Qualification",
        "##계획서번호##": "VP-IQ-PB-001",
        "##보고서번호##": "VR-IQ-PB-001",
        "##해당년도##": "2026",
    }
    assert request.output_filename() == "Pass Box_IOQ_cover.pdf"


def test_cover_qualification_mapping_matches_all_requested_values() -> None:
    assert list(QUALIFICATION_TITLES) == ["URS", "F&DS", "DQ", "FAT", "SAT", "IQ", "OQ", "IOQ", "PQ", "CD", "CV"]
    assert QUALIFICATION_TITLES["URS"] == ("사용자 요구규격서", "User Requirement Specification")
    assert QUALIFICATION_TITLES["F&DS"] == ("기능 및 설계 규격서", "Functional & Design Specification")
    assert QUALIFICATION_TITLES["IQ"][1] == "Installation Qualification"
    assert QUALIFICATION_TITLES["OQ"][1] == "Operational Qualification"
    assert QUALIFICATION_TITLES["CV"] == ("과산화수소증기 사이클 검증", "Cycle Validation")


def test_cover_logo_placements_match_requested_dimensions() -> None:
    assert tuple(item.token for item in LOGO_PLACEMENTS) == LOGO_PLACEHOLDERS
    assert [(item.dimension, item.centimetres) for item in LOGO_PLACEMENTS] == [
        ("height", 2.11),
        ("width", 1.38),
        ("width", 2.4),
        ("width", 3.58),
        ("width", 3.58),
    ]


def test_cover_generator_merges_two_single_page_exports_in_order(tmp_path: Path) -> None:
    renderer = FakeCoverRenderer()

    output = CoverPdfGenerator(renderer).generate(_request(tmp_path))

    assert output.name == "Pass Box_IQ_cover.pdf"
    assert renderer.request is not None
    with fitz.open(output) as document:
        assert document.page_count == 2


def test_cover_generator_rejects_a_sheet_that_exports_to_multiple_pages(tmp_path: Path) -> None:
    with pytest.raises(RuntimeError, match="개별라벨.*2페이지"):
        CoverPdfGenerator(FakeCoverRenderer((1, 2))).generate(_request(tmp_path))


def test_cover_request_requires_english_equipment_name(tmp_path: Path) -> None:
    request = _request(tmp_path)
    invalid = CoverDocumentRequest(
        request.template_path,
        request.customer_logo_path,
        request.output_directory,
        "패스박스",
        request.qualification_abbreviation,
        request.plan_number,
        request.report_number,
        request.applicable_year,
    )

    assert "장비명은 영문으로 작성해 주세요." in invalid.validation_errors()


def test_cover_request_requires_report_number(tmp_path: Path) -> None:
    request = _request(tmp_path)
    invalid = CoverDocumentRequest(
        request.template_path,
        request.customer_logo_path,
        request.output_directory,
        request.equipment_name,
        request.qualification_abbreviation,
        request.plan_number,
        "",
        request.applicable_year,
    )

    assert "보고서번호를 입력해 주세요." in invalid.validation_errors()


def test_cover_widget_exposes_requested_inputs_and_drag_drop(tmp_path: Path, qapp) -> None:  # type: ignore[no-untyped-def]
    from vegas_doc.builtin_plugins.cover_generator import CoverGeneratorWidget
    from vegas_doc.config.defaults import AppSettings
    from vegas_doc.core.application_context import build_application_context

    widget = CoverGeneratorWidget(build_application_context(AppSettings(), data_dir=tmp_path / "data"))
    widget.equipment_name.setText("Pass Box")
    widget.qualification.setCurrentText("CV")
    widget.report_number.setText("VR-CV-PB-001")

    assert widget.equipment_name.placeholderText() == "영문으로 작성하세요."
    assert [widget.qualification.itemText(index) for index in range(widget.qualification.count())] == list(QUALIFICATION_TITLES)
    assert widget.qualification_korean.text() == "과산화수소증기 사이클 검증"
    assert widget.qualification_english.text() == "Cycle Validation"
    assert widget.report_number.text() == "VR-CV-PB-001"
    assert widget.filename_preview.text() == "Pass Box_CV_cover.pdf"
    assert widget.print_button.text() == "Print"
    assert not any("cm" in label.text().lower() for label in widget.findChildren(QLabel))
    assert widget.template_input.acceptDrops()
    assert widget.logo_input.acceptDrops()


def test_cover_print_does_not_require_a_pdf_output_directory(tmp_path: Path, qapp, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    from vegas_doc.builtin_plugins.cover_generator import CoverGeneratorWidget
    from vegas_doc.config.defaults import AppSettings
    from vegas_doc.core.application_context import build_application_context

    request = _request(tmp_path)
    widget = CoverGeneratorWidget(build_application_context(AppSettings(), data_dir=tmp_path / "data"))
    widget.template_input.set_path(request.template_path)
    widget.logo_input.set_path(request.customer_logo_path)
    widget.equipment_name.setText(request.equipment_name)
    widget.qualification.setCurrentText(request.qualification_abbreviation)
    widget.plan_number.setText(request.plan_number)
    widget.report_number.setText(request.report_number)
    widget.applicable_year.setText(request.applicable_year)
    observed: dict[str, object] = {}

    def start_generation(print_request: CoverDocumentRequest, operation: str) -> None:
        observed["request"] = print_request
        observed["operation"] = operation
        observed["temporary_directory_exists"] = print_request.output_directory.is_dir()

    monkeypatch.setattr(widget, "_start_generation", start_generation)
    widget.print_cover()

    assert observed["operation"] == "print"
    assert observed["temporary_directory_exists"] is True
    print_request = observed["request"]
    assert isinstance(print_request, CoverDocumentRequest)
    assert print_request.output_directory != request.output_directory
    widget._cleanup_print_directory()
    assert not print_request.output_directory.exists()


class _PrintDialogResult:
    def __init__(self, result: QDialog.DialogCode) -> None:
        self.result = result
        self.title = ""
        self.page_range = (0, 0)

    def setWindowTitle(self, title: str) -> None:  # noqa: N802 - mirrors Qt API.
        self.title = title

    def setMinMax(self, minimum: int, maximum: int) -> None:  # noqa: N802 - mirrors Qt API.
        self.page_range = (minimum, maximum)

    def exec(self) -> int:
        return self.result


def test_cover_printer_renders_two_pages_after_print_dialog_confirmation(tmp_path: Path, qapp) -> None:  # type: ignore[no-untyped-def]
    source = tmp_path / "cover.pdf"
    output = tmp_path / "printed.pdf"
    document = fitz.open()
    document.new_page(width=595, height=842).insert_text((72, 72), "Cover page")
    document.new_page(width=595, height=842).insert_text((72, 72), "Label page")
    document.save(source)
    document.close()
    printer = QPrinter(QPrinter.PrinterMode.HighResolution)
    printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
    printer.setOutputFileName(str(output))
    printer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
    dialog = _PrintDialogResult(QDialog.DialogCode.Accepted)
    service = CoverPdfPrinter(
        printer_factory=lambda: printer,
        dialog_factory=lambda _printer, _parent: dialog,
        render_dpi=96,
    )

    assert service.print_pdf(source)
    assert dialog.title == "Cover 인쇄"
    assert dialog.page_range == (1, 2)
    with fitz.open(output) as printed:
        assert printed.page_count == 2


def test_cover_printer_cancel_does_not_create_output(tmp_path: Path, qapp) -> None:  # type: ignore[no-untyped-def]
    source = tmp_path / "cover.pdf"
    output = tmp_path / "printed.pdf"
    document = fitz.open()
    document.new_page()
    document.save(source)
    document.close()
    printer = QPrinter(QPrinter.PrinterMode.HighResolution)
    printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
    printer.setOutputFileName(str(output))
    dialog = _PrintDialogResult(QDialog.DialogCode.Rejected)
    service = CoverPdfPrinter(
        printer_factory=lambda: printer,
        dialog_factory=lambda _printer, _parent: dialog,
    )

    assert not service.print_pdf(source)
    assert not output.exists()


def test_excel_renderer_script_preserves_template_and_exports_two_sheets() -> None:
    script = (ROOT / "src" / "vegas_doc" / "resources" / "scripts" / "render_cover.ps1").read_text(
        encoding="utf-8"
    )
    spec = (ROOT / "Vegas_Total_Solution_Doc.spec").read_text(encoding="utf-8")

    assert "Excel.Application" in script
    assert 'Invoke-ComMethod $workbooks "Open" @([string]$request.template_path, 0, $true)' in script
    assert 'Set-ComProperty $pageSetup "FitToPagesWide" 1' in script
    assert 'Set-ComProperty $pageSetup "FitToPagesTall" 1' in script
    assert "ExportAsFixedFormat" in script
    assert 'Invoke-ComMethod $shapes "AddPicture"' in script and '"LockAspectRatio" -1' in script
    assert "foreach ($shape in $originalShapes)" in script
    assert 'Get-ComItem $shapes' not in script
    assert 'Invoke-ComMethod $workbook "Close" @($false)' in script
    assert '"resources/scripts/*.ps1"' in spec
