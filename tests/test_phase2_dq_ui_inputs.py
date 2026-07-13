"""Phase 2 DQ input model and real UI tests."""

from __future__ import annotations

from datetime import date
from pathlib import Path

from PySide6.QtWidgets import QLineEdit

from vegas_doc.models.dq_document_data import DQDocumentData, section_key
from vegas_doc.utils.date_format import format_document_date


def test_section_numbers_compare_numerically() -> None:
    assert section_key("6.9") < section_key("6.10")
    assert section_key("6.4") < section_key("6.4.1")
    assert format_document_date(date(2026, 7, 13)) == "2026.07.13"


def test_safe_default_output_filename(tmp_path: Path) -> None:
    data = DQDocumentData(
        tmp_path / "logo.png",
        tmp_path / "template.docx",
        tmp_path / "urs.pdf",
        "DQ:26001",
        "1.0",
        "Weighing/Booth",
        "Tester",
        date(2026, 7, 12),
        "과장",
        "Vegas Inc.",
        "6.4",
        "6.8",
        tmp_path,
    )
    assert data.resolved_output_filename() == "DQ_26001_Weighing_Booth_DQ_2026.07.12.docx"


def test_validation_reports_required_fields_and_bad_range(tmp_path: Path) -> None:
    data = DQDocumentData(
        Path(""),
        Path(""),
        Path(""),
        "",
        "",
        "",
        "",
        date.today(),
        "",
        "",
        "6.10",
        "6.9",
        tmp_path,
    )
    errors = data.validation_errors(require_existing_files=False)
    assert any("문서번호" in error for error in errors)
    assert any("시작 요구사항 번호는 종료 번호보다 클 수 없습니다" in error for error in errors)


def test_real_dq_widget_contains_phase2_inputs(tmp_path: Path) -> None:
    from conftest import require_qt

    require_qt()
    from vegas_doc.builtin_plugins.dq_generator import DQGeneratorWidget
    from vegas_doc.config.defaults import AppSettings
    from vegas_doc.core.application_context import build_application_context

    widget = DQGeneratorWidget(build_application_context(AppSettings(), data_dir=tmp_path))
    assert widget.author_date.calendarPopup()
    assert widget.logo_input.acceptDrops()
    assert widget.template_input.acceptDrops()
    assert widget.urs_input.acceptDrops()
    assert widget.start_requirement.text() == "6.4"
    assert widget.end_requirement.text() == "6.8"
    assert isinstance(widget.author_position, QLineEdit)
    widget.author_position.setText("품질보증 책임자")
    assert widget.author_position.text() == "품질보증 책임자"
    assert widget.author_date.displayFormat() == "yyyy.MM.dd"
    assert widget.page_review.minimumHeight() >= 320
    assert widget.table.minimumHeight() >= 480
