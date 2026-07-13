"""Shared user acknowledgement before saving OCR-derived documents."""

from __future__ import annotations

from PySide6.QtWidgets import QMessageBox, QWidget


OCR_DOCUMENT_REVIEW_WARNING = (
    "자동 생성기는 페이지 번호를 식별하지 못합니다. "
    "반드시 페이지 번호를 확인하시고, OCR 기능을 맹신하지 마세요. "
    "문서를 반드시 검토하세요."
)


def confirm_ocr_document_review(parent: QWidget) -> bool:
    """Return whether the user acknowledged the mandatory review warning."""

    answer = QMessageBox.warning(
        parent,
        "문서 검토 경고",
        OCR_DOCUMENT_REVIEW_WARNING,
        QMessageBox.Ok | QMessageBox.Cancel,
        QMessageBox.Cancel,
    )
    return answer == QMessageBox.Ok
