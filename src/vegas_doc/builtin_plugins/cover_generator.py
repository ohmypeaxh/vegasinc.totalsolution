"""Cover Generator plugin for Excel-based two-page PDF covers."""

from __future__ import annotations

import logging
import shutil
import tempfile
from dataclasses import replace
from pathlib import Path

from PySide6.QtCore import QObject, QThread, QUrl, Signal
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from vegas_doc.core.application_context import ApplicationContext
from vegas_doc.models.cover_document import QUALIFICATION_TITLES, CoverDocumentRequest
from vegas_doc.plugins.plugin import Plugin, PluginMetadata
from vegas_doc.services.cover_generator import CoverPdfGenerator
from vegas_doc.services.cover_printer import CoverPdfPrinter
from vegas_doc.ui.widgets.file_path_input import FilePathInput


class CoverGenerationWorker(QObject):
    """Run Excel automation outside the UI thread."""

    completed = Signal(str)
    failed = Signal(str)

    def __init__(self, request: CoverDocumentRequest, context: ApplicationContext) -> None:
        super().__init__()
        self._request = request
        self._context = context

    def run(self) -> None:
        """Generate the PDF and report errors at the worker boundary."""

        try:
            output_path = CoverPdfGenerator().generate(self._request)
        except Exception as error:  # noqa: BLE001 - worker boundary isolates Excel failures.
            self._context.services.resolve(logging.Logger).exception("Cover PDF generation failed")
            self.failed.emit(str(error))
            return
        self.completed.emit(str(output_path))


class CoverGeneratorWidget(QWidget):
    """Collect cover values and generate a real two-page PDF from Excel."""

    def __init__(self, context: ApplicationContext) -> None:
        super().__init__()
        self._context = context
        self._thread: QThread | None = None
        self._worker: CoverGenerationWorker | None = None
        self._operation: str | None = None
        self._print_temporary_directory: Path | None = None
        self._printer = CoverPdfPrinter()
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(8)

        eyebrow = QLabel("EXCEL COVER AUTOMATION")
        eyebrow.setObjectName("Eyebrow")
        title = QLabel("Cover Generator")
        title.setObjectName("PageTitle")
        subtitle = QLabel("개별표지와 개별라벨 시트를 치환하여 하나의 2페이지 PDF로 생성합니다.")
        subtitle.setObjectName("PageSubtitle")
        root.addWidget(eyebrow)
        root.addWidget(title)
        root.addWidget(subtitle)
        root.addSpacing(10)

        scroll = QScrollArea()
        scroll.setObjectName("CoverWorkspaceScroll")
        scroll.setWidgetResizable(True)
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(4, 4, 12, 20)
        layout.setSpacing(12)

        document_group = QGroupBox("A. 표지 정보")
        form = QFormLayout(document_group)
        self.equipment_name = QLineEdit()
        self.equipment_name.setPlaceholderText("영문으로 작성하세요.")
        self.qualification = QComboBox()
        self.qualification.addItems(tuple(QUALIFICATION_TITLES))
        self.qualification_korean = QLabel()
        self.qualification_korean.setObjectName("DocumentPreview")
        self.qualification_english = QLabel()
        self.qualification_english.setObjectName("DocumentPreview")
        self.qualification_english.setWordWrap(True)
        self.qualification.currentTextChanged.connect(self._update_qualification_preview)
        self.plan_number = QLineEdit()
        self.report_number = QLineEdit()
        self.applicable_year = QLineEdit()
        self.applicable_year.setPlaceholderText("예: 2026")
        form.addRow("장비명 *", self.equipment_name)
        form.addRow("적격성평가축약 *", self.qualification)
        form.addRow("적격성평가한글", self.qualification_korean)
        form.addRow("적격성평가영문", self.qualification_english)
        form.addRow("계획서번호 *", self.plan_number)
        form.addRow("보고서번호 *", self.report_number)
        form.addRow("해당년도 *", self.applicable_year)
        layout.addWidget(document_group)

        assets_group = QGroupBox("B. Excel 템플릿 및 고객사 로고")
        assets_form = QFormLayout(assets_group)
        self.template_input = FilePathInput(
            extensions=(".xlsx",),
            dialog_filter="Excel workbook (*.xlsx)",
            drop_text="개별표지·개별라벨 시트가 있는 XLSX 파일을 끌어 놓으세요.",
        )
        self.logo_input = FilePathInput(
            extensions=(".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff"),
            dialog_filter="Logo images (*.png *.jpg *.jpeg *.bmp *.tif *.tiff)",
            drop_text="고객사 로고 이미지를 끌어 놓으세요.",
        )
        excel_help = QLabel("PDF 변환에는 Microsoft Excel이 설치된 Windows PC가 필요합니다. 템플릿 원본은 변경하지 않습니다.")
        excel_help.setObjectName("MutedText")
        excel_help.setWordWrap(True)
        assets_form.addRow("Excel XLSX 템플릿 *", self.template_input)
        assets_form.addRow("고객사 로고 *", self.logo_input)
        assets_form.addRow("", excel_help)
        layout.addWidget(assets_group)

        output_group = QGroupBox("C. PDF 출력")
        output_form = QFormLayout(output_group)
        self.output_directory = FilePathInput(mode="directory", drop_text="PDF 저장 폴더를 선택하세요.")
        self.filename_preview = QLabel()
        self.filename_preview.setObjectName("DocumentPreview")
        self.equipment_name.textChanged.connect(self._update_filename_preview)
        self.qualification.currentTextChanged.connect(self._update_filename_preview)
        output_form.addRow("PDF 저장 위치 *", self.output_directory)
        output_form.addRow("저장 파일명", self.filename_preview)
        print_help = QLabel("Print는 PDF 저장 위치를 사용하지 않으며 인쇄 후 임시 파일을 자동으로 삭제합니다.")
        print_help.setObjectName("MutedText")
        print_help.setWordWrap(True)
        output_form.addRow("", print_help)
        layout.addWidget(output_group)

        self.generate_button = QPushButton("Cover PDF 생성")
        self.generate_button.setObjectName("PrimaryAction")
        self.generate_button.clicked.connect(self.generate_pdf)
        self.print_button = QPushButton("Print")
        self.print_button.setMinimumWidth(100)
        self.print_button.clicked.connect(self.print_cover)
        action_layout = QHBoxLayout()
        action_layout.setSpacing(10)
        action_layout.addWidget(self.generate_button)
        action_layout.addWidget(self.print_button)
        action_layout.addStretch()
        layout.addLayout(action_layout)
        self.status = QLabel("필수 정보와 Excel 템플릿을 선택해 주세요.")
        self.status.setObjectName("StatusText")
        self.status.setWordWrap(True)
        layout.addWidget(self.status)
        layout.addStretch()

        scroll.setWidget(content)
        root.addWidget(scroll, 1)
        self._update_qualification_preview(self.qualification.currentText())
        self._update_filename_preview()

    def current_request(self) -> CoverDocumentRequest:
        """Build an immutable generation request from visible form values."""

        return CoverDocumentRequest(
            template_path=Path(self.template_input.path()),
            customer_logo_path=Path(self.logo_input.path()),
            output_directory=Path(self.output_directory.path()),
            equipment_name=self.equipment_name.text().strip(),
            qualification_abbreviation=self.qualification.currentText(),
            plan_number=self.plan_number.text().strip(),
            report_number=self.report_number.text().strip(),
            applicable_year=self.applicable_year.text().strip(),
        )

    def generate_pdf(self) -> None:
        """Validate the form and start Excel/PDF generation."""

        if self._thread is not None and self._thread.isRunning():
            QMessageBox.information(self, "PDF 생성 중", "이미 Cover PDF를 생성하고 있습니다.")
            return
        request = self.current_request()
        errors = request.validation_errors()
        if errors:
            QMessageBox.warning(self, "생성 전 확인", "\n".join(dict.fromkeys(errors)))
            return
        self._start_generation(request, "save")

    def print_cover(self) -> None:
        """Prepare a temporary Cover PDF and open the native Windows print dialog."""

        if self._thread is not None and self._thread.isRunning():
            QMessageBox.information(self, "Cover 작업 중", "이미 Cover 문서를 처리하고 있습니다.")
            return
        request = self.current_request()
        errors = request.validation_errors(require_output_directory=False)
        if errors:
            QMessageBox.warning(self, "인쇄 전 확인", "\n".join(dict.fromkeys(errors)))
            return
        self._print_temporary_directory = Path(tempfile.mkdtemp(prefix="vegas_cover_print_"))
        print_request = replace(request, output_directory=self._print_temporary_directory)
        self._start_generation(print_request, "print")

    def _start_generation(self, request: CoverDocumentRequest, operation: str) -> None:
        """Start the shared Excel rendering worker for save or direct print."""

        self._operation = operation
        self.generate_button.setEnabled(False)
        self.print_button.setEnabled(False)
        if operation == "print":
            self.print_button.setText("인쇄 준비 중...")
            self.status.setText("Excel 자리표시자를 변경하고 인쇄 데이터를 준비하고 있습니다...")
        else:
            self.generate_button.setText("PDF 생성 중...")
            self.status.setText("Excel 자리표시자를 변경하고 2페이지 PDF를 생성하고 있습니다...")
        self._thread = QThread(self)
        self._worker = CoverGenerationWorker(request, self._context)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.completed.connect(self._on_completed)
        self._worker.failed.connect(self._on_failed)
        self._worker.completed.connect(self._thread.quit)
        self._worker.failed.connect(self._thread.quit)
        self._thread.finished.connect(self._worker.deleteLater)
        self._thread.finished.connect(self._cleanup_worker)
        self._thread.start()

    def _on_completed(self, output_path: str) -> None:
        path = Path(output_path)
        if self._operation == "print":
            self._print_generated_pdf(path)
            return
        self.status.setText(f"Cover PDF를 생성했습니다: {path}")
        answer = QMessageBox.question(self, "생성 완료", f"2페이지 Cover PDF 생성 완료!\n\n{path}\n\n파일을 바로 열까요?")
        if answer == QMessageBox.StandardButton.Yes:
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))

    def _on_failed(self, message: str) -> None:
        if self._operation == "print":
            self.status.setText("Cover 인쇄 준비에 실패했습니다.")
            QMessageBox.critical(self, "Cover 인쇄 오류", message)
        else:
            self.status.setText("Cover PDF 생성에 실패했습니다.")
            QMessageBox.critical(self, "Cover PDF 생성 오류", message)

    def _print_generated_pdf(self, path: Path) -> None:
        """Open the print dialog for the temporary generated document."""

        self.status.setText("Windows 인쇄 창에서 프린터와 인쇄 옵션을 선택해 주세요.")
        try:
            printed = self._printer.print_pdf(path, self)
        except Exception as error:  # noqa: BLE001 - UI boundary reports printer failures.
            self._context.services.resolve(logging.Logger).exception("Cover printing failed")
            self.status.setText("Cover 인쇄에 실패했습니다.")
            QMessageBox.critical(self, "Cover 인쇄 오류", str(error))
        else:
            self.status.setText("Cover 인쇄 작업을 전송했습니다." if printed else "Cover 인쇄를 취소했습니다.")
        finally:
            self._cleanup_print_directory()

    def _cleanup_worker(self) -> None:
        if self._thread is not None:
            self._thread.deleteLater()
        self._worker = None
        self._thread = None
        self.generate_button.setEnabled(True)
        self.print_button.setEnabled(True)
        self.generate_button.setText("Cover PDF 생성")
        self.print_button.setText("Print")
        self._operation = None
        self._cleanup_print_directory()

    def _cleanup_print_directory(self) -> None:
        if self._print_temporary_directory is not None:
            temporary_directory = self._print_temporary_directory
            self._print_temporary_directory = None
            try:
                shutil.rmtree(temporary_directory)
            except OSError:
                self._context.services.resolve(logging.Logger).exception(
                    "Could not remove temporary Cover print directory: %s", temporary_directory
                )
                self.status.setText(
                    f"{self.status.text()} 임시 인쇄 파일을 삭제하지 못했습니다: {temporary_directory}"
                )

    def _update_qualification_preview(self, abbreviation: str) -> None:
        korean, english = QUALIFICATION_TITLES.get(abbreviation, ("", ""))
        self.qualification_korean.setText(korean)
        self.qualification_english.setText(english)

    def _update_filename_preview(self, *_args: object) -> None:
        equipment = self.equipment_name.text().strip() or "장비명"
        self.filename_preview.setText(f"{equipment}_{self.qualification.currentText()}_cover.pdf")


class CoverGeneratorPlugin(Plugin):
    """Production Cover Generator plugin."""

    metadata = PluginMetadata("cover", "Cover Generator", "Create two-page cover PDFs from Excel templates.", 50)

    def create_widget(self, context: ApplicationContext) -> QWidget:
        return CoverGeneratorWidget(context)


def create_plugin() -> Plugin:
    """Return the Cover Generator plugin."""

    return CoverGeneratorPlugin()
