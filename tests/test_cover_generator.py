"""Cover Generator mappings, PDF composition, and UI tests."""

from __future__ import annotations

from pathlib import Path

import fitz
import pytest

from vegas_doc.models.cover_document import (
    LOGO_PLACEHOLDERS,
    QUALIFICATION_TITLES,
    TEXT_PLACEHOLDERS,
    CoverDocumentRequest,
)
from vegas_doc.services.cover_generator import LOGO_PLACEMENTS, CoverPdfGenerator


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
        "##해당년도##": "2026",
    }
    assert request.output_filename() == "Pass Box_IOQ_cover.pdf"


def test_cover_qualification_mapping_matches_all_requested_values() -> None:
    assert list(QUALIFICATION_TITLES) == ["URS", "F&DS", "DQ", "FAT", "SAT", "IQ", "OQ", "IOQ", "PQ", "CD", "CV"]
    assert QUALIFICATION_TITLES["URS"] == ("사용자 요구규격서", "User Requirement Specification")
    assert QUALIFICATION_TITLES["F&DS"] == ("기능 및 설계 규격서", "Functional & Design Specification")
    assert QUALIFICATION_TITLES["IQ"][1] == "Installation Qualifiaction"
    assert QUALIFICATION_TITLES["OQ"][1] == "Operational Qualificiation"
    assert QUALIFICATION_TITLES["CV"] == ("과산화수소증기 사이클 검증", "Cycle Validation")


def test_cover_logo_placements_match_requested_dimensions() -> None:
    assert tuple(item.token for item in LOGO_PLACEMENTS) == LOGO_PLACEHOLDERS
    assert [(item.dimension, item.centimetres) for item in LOGO_PLACEMENTS] == [
        ("height", 2.11),
        ("width", 1.38),
        ("width", 2.4),
        ("width", 2.4),
        ("width", 2.4),
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
        request.applicable_year,
    )

    assert "장비명은 영문으로 작성해 주세요." in invalid.validation_errors()


def test_cover_widget_exposes_requested_inputs_and_drag_drop(tmp_path: Path, qapp) -> None:  # type: ignore[no-untyped-def]
    from vegas_doc.builtin_plugins.cover_generator import CoverGeneratorWidget
    from vegas_doc.config.defaults import AppSettings
    from vegas_doc.core.application_context import build_application_context

    widget = CoverGeneratorWidget(build_application_context(AppSettings(), data_dir=tmp_path / "data"))
    widget.equipment_name.setText("Pass Box")
    widget.qualification.setCurrentText("CV")

    assert widget.equipment_name.placeholderText() == "영문으로 작성하세요."
    assert [widget.qualification.itemText(index) for index in range(widget.qualification.count())] == list(QUALIFICATION_TITLES)
    assert widget.qualification_korean.text() == "과산화수소증기 사이클 검증"
    assert widget.qualification_english.text() == "Cycle Validation"
    assert widget.filename_preview.text() == "Pass Box_CV_cover.pdf"
    assert widget.template_input.acceptDrops()
    assert widget.logo_input.acceptDrops()


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
    assert 'Invoke-ComMethod $workbook "Close" @($false)' in script
    assert '"resources/scripts/*.ps1"' in spec
