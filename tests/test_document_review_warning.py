"""Mandatory acknowledgement shown before saving OCR-derived documents."""

from __future__ import annotations

from PySide6.QtWidgets import QMessageBox, QWidget

from vegas_doc.ui.document_review_warning import OCR_DOCUMENT_REVIEW_WARNING, confirm_ocr_document_review


def test_document_review_warning_uses_requested_text_and_allows_cancel(qapp, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    captured: list[tuple[str, str]] = []

    def cancel(_parent, title, text, *_args):  # type: ignore[no-untyped-def]
        captured.append((title, text))
        return QMessageBox.Cancel

    monkeypatch.setattr(QMessageBox, "warning", cancel)

    assert not confirm_ocr_document_review(QWidget())
    assert captured == [("문서 검토 경고", OCR_DOCUMENT_REVIEW_WARNING)]
    assert OCR_DOCUMENT_REVIEW_WARNING == (
        "자동 생성기는 페이지 번호를 식별하지 못합니다. "
        "반드시 페이지 번호를 확인하시고, OCR 기능을 맹신하지 마세요. "
        "문서를 반드시 검토하세요."
    )

    monkeypatch.setattr(QMessageBox, "warning", lambda *_args: QMessageBox.Ok)
    assert confirm_ocr_document_review(QWidget())
