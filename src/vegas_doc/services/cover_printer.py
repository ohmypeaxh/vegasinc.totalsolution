"""Native printer-dialog support for generated Cover PDFs."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Protocol

import fitz
from PySide6.QtCore import QRectF
from PySide6.QtGui import QImage, QPainter
from PySide6.QtPrintSupport import QPrinter, QPrintDialog
from PySide6.QtWidgets import QDialog, QWidget


class PrintDialog(Protocol):
    """Small abstraction around the native Qt print dialog."""

    def setWindowTitle(self, title: str) -> None:  # noqa: N802 - Qt API naming.
        """Set the dialog title."""

    def setMinMax(self, minimum: int, maximum: int) -> None:  # noqa: N802 - Qt API naming.
        """Set the selectable PDF page range."""

    def exec(self) -> int:
        """Show the modal dialog and return its result."""


PrinterFactory = Callable[[], QPrinter]
DialogFactory = Callable[[QPrinter, QWidget | None], PrintDialog]


class CoverPdfPrinter:
    """Show the native print dialog and send every selected PDF page to a printer."""

    def __init__(
        self,
        *,
        printer_factory: PrinterFactory | None = None,
        dialog_factory: DialogFactory | None = None,
        render_dpi: int = 300,
    ) -> None:
        self._printer_factory = printer_factory or _high_resolution_printer
        self._dialog_factory = dialog_factory or QPrintDialog
        self._render_dpi = render_dpi

    def print_pdf(self, pdf_path: Path, parent: QWidget | None = None) -> bool:
        """Print a PDF after user confirmation; return ``False`` when cancelled."""

        if not pdf_path.is_file():
            raise FileNotFoundError(f"인쇄할 Cover 문서를 찾을 수 없습니다: {pdf_path}")
        with fitz.open(pdf_path) as document:
            page_count = document.page_count
        if page_count < 1:
            raise RuntimeError("인쇄할 Cover 문서에 페이지가 없습니다.")

        printer = self._printer_factory()
        printer.setDocName(pdf_path.stem)
        dialog = self._dialog_factory(printer, parent)
        dialog.setWindowTitle("Cover 인쇄")
        dialog.setMinMax(1, page_count)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return False

        first_page, last_page = _selected_page_range(printer, page_count)
        self._render_to_printer(pdf_path, printer, first_page, last_page)
        return True

    def _render_to_printer(self, pdf_path: Path, printer: QPrinter, first_page: int, last_page: int) -> None:
        painter = QPainter()
        if not painter.begin(printer):
            raise RuntimeError("선택한 프린터에서 인쇄 작업을 시작할 수 없습니다.")
        try:
            with fitz.open(pdf_path) as document:
                for output_index, page_index in enumerate(range(first_page, last_page + 1)):
                    if output_index and not printer.newPage():
                        raise RuntimeError("프린터에서 다음 페이지를 준비하지 못했습니다.")
                    image = _render_page(document[page_index], self._render_dpi)
                    bounds = printer.pageRect(QPrinter.Unit.DevicePixel)
                    target = _fit_rect(image.width(), image.height(), bounds)
                    painter.drawImage(target, image)
        finally:
            if painter.isActive():
                painter.end()


def _high_resolution_printer() -> QPrinter:
    return QPrinter(QPrinter.PrinterMode.HighResolution)


def _selected_page_range(printer: QPrinter, page_count: int) -> tuple[int, int]:
    from_page = printer.fromPage()
    to_page = printer.toPage()
    if from_page <= 0 or to_page <= 0:
        return 0, page_count - 1
    first = min(max(from_page - 1, 0), page_count - 1)
    last = min(max(to_page - 1, first), page_count - 1)
    return first, last


def _render_page(page: fitz.Page, dpi: int) -> QImage:
    scale = max(dpi, 72) / 72
    pixmap = page.get_pixmap(matrix=fitz.Matrix(scale, scale), alpha=False)
    image = QImage(
        pixmap.samples,
        pixmap.width,
        pixmap.height,
        pixmap.stride,
        QImage.Format.Format_RGB888,
    )
    return image.copy()


def _fit_rect(source_width: int, source_height: int, bounds: QRectF) -> QRectF:
    if source_width <= 0 or source_height <= 0 or bounds.width() <= 0 or bounds.height() <= 0:
        raise RuntimeError("프린터의 출력 가능 영역을 확인할 수 없습니다.")
    scale = min(bounds.width() / source_width, bounds.height() / source_height)
    width = source_width * scale
    height = source_height * scale
    return QRectF(
        bounds.x() + (bounds.width() - width) / 2,
        bounds.y() + (bounds.height() - height) / 2,
        width,
        height,
    )
