"""Raw Data Generator plugin for HEPA and ordered two-picture Word layouts."""

from __future__ import annotations

import logging
from pathlib import Path

from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFormLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from vegas_doc.core.application_context import ApplicationContext
from vegas_doc.models.raw_data_document import QualificationType, RawDataDocumentRequest, RawDataType
from vegas_doc.plugins.plugin import Plugin, PluginMetadata
from vegas_doc.services.raw_data_generator import PICTURE_TOKEN, RawDataDocumentGenerator
from vegas_doc.ui.widgets.file_path_input import FilePathInput
from vegas_doc.ui.widgets.image_list_input import ImageListInput


class RawDataGeneratorWidget(QWidget):
    """Collect Raw Data inputs and delegate DOCX rendering to the document service."""

    def __init__(self, context: ApplicationContext) -> None:
        super().__init__()
        self._context = context
        self._generator = RawDataDocumentGenerator()
        self._build_ui()
        self._on_type_changed()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(8)

        eyebrow = QLabel("QUALIFICATION RAW DATA")
        eyebrow.setObjectName("Eyebrow")
        title = QLabel("Raw Data Generator")
        title.setObjectName("PageTitle")
        subtitle = QLabel("Raw Data 형식과 적격성평가 종류를 선택하고 실제 Word 템플릿으로 결과 문서를 생성합니다.")
        subtitle.setObjectName("PageSubtitle")
        root.addWidget(eyebrow)
        root.addWidget(title)
        root.addWidget(subtitle)
        root.addSpacing(10)

        scroll = QScrollArea()
        scroll.setObjectName("RawDataWorkspaceScroll")
        scroll.setWidgetResizable(True)
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(4, 4, 12, 20)
        content_layout.setSpacing(12)

        document_group = QGroupBox("A. 문서 정보")
        document_form = QFormLayout(document_group)
        self.raw_data_type = QComboBox()
        self.raw_data_type.addItems([item.value for item in RawDataType])
        self.raw_data_type.currentIndexChanged.connect(self._on_type_changed)
        self.qualification_type = QComboBox()
        self.qualification_type.addItems([item.value for item in QualificationType])
        self.document_number = QLineEdit()
        self.document_number.setPlaceholderText("예: MD-RD-PB01-26")
        self.logo_input = FilePathInput(
            extensions=(".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff"),
            dialog_filter="Logo images (*.png *.jpg *.jpeg *.bmp *.tif *.tiff)",
            drop_text="회사 로고 이미지를 끌어 놓으세요.",
        )
        document_form.addRow("Raw Data Type *", self.raw_data_type)
        document_form.addRow("적격성평가 종류 *", self.qualification_type)
        document_form.addRow("문서번호 *", self.document_number)
        document_form.addRow("회사 로고 *", self.logo_input)
        content_layout.addWidget(document_group)

        mode_group = QGroupBox("B. Raw Data 형식별 설정")
        mode_form = QFormLayout(mode_group)
        self.hepa_count_label = QLabel("HEPA FILTER 개수 *")
        self.hepa_filter_count = QSpinBox()
        self.hepa_filter_count.setRange(1, 999)
        self.hepa_filter_count.setValue(1)
        self.verification_name_label = QLabel("검증명")
        self.verification_name = QLineEdit()
        self.verification_name.setPlaceholderText("사진형 Raw Data의 검증명을 입력하세요.")
        mode_form.addRow(self.hepa_count_label, self.hepa_filter_count)
        mode_form.addRow(self.verification_name_label, self.verification_name)
        content_layout.addWidget(mode_group)

        self.pictures_group = QGroupBox("C. 첨부사진 및 순서")
        pictures_layout = QVBoxLayout(self.pictures_group)
        self.picture_help = QLabel()
        self.picture_help.setObjectName("MutedText")
        self.picture_help.setWordWrap(True)
        self.image_list = ImageListInput()
        pictures_layout.addWidget(self.picture_help)
        pictures_layout.addWidget(self.image_list)
        content_layout.addWidget(self.pictures_group)

        files_group = QGroupBox("D. Word 템플릿 및 저장")
        files_form = QFormLayout(files_group)
        self.template_input = FilePathInput(
            extensions=(".docx",),
            dialog_filter="Word documents (*.docx)",
            drop_text="Raw Data Word 템플릿을 끌어 놓으세요.",
        )
        self.output_directory = FilePathInput(mode="directory", drop_text="Word 저장 폴더를 선택하세요.")
        files_form.addRow("Word 템플릿 *", self.template_input)
        files_form.addRow("Word 저장 위치 *", self.output_directory)
        placeholder_help = QLabel(
            "공통 Placeholder: ##적격성종류##, ##문서번호##, ##로고##  |  "
            f"HEPA: ##HEPA번호##가 포함된 표  |  사진형: ##검증명##, {PICTURE_TOKEN}"
        )
        placeholder_help.setObjectName("MutedText")
        placeholder_help.setWordWrap(True)
        files_form.addRow("", placeholder_help)
        content_layout.addWidget(files_group)

        self.generate_button = QPushButton("Raw Data Word 생성")
        self.generate_button.setObjectName("PrimaryButton")
        self.generate_button.clicked.connect(self.generate_document)
        content_layout.addWidget(self.generate_button)
        self.status = QLabel("필수 항목과 Word 템플릿을 선택해 주세요.")
        self.status.setObjectName("StatusText")
        self.status.setWordWrap(True)
        content_layout.addWidget(self.status)
        content_layout.addStretch()

        scroll.setWidget(content)
        root.addWidget(scroll, 1)

    def _on_type_changed(self) -> None:
        selected = self.selected_raw_data_type()
        is_hepa = selected is RawDataType.HEPA_FILTER
        self.hepa_count_label.setEnabled(is_hepa)
        self.hepa_filter_count.setEnabled(is_hepa)
        self.verification_name_label.setEnabled(not is_hepa)
        self.verification_name.setEnabled(not is_hepa)
        self.pictures_group.setEnabled(not is_hepa)
        if selected is RawDataType.TWO_CUT_COMMENT:
            self.picture_help.setText(
                "사진을 여러 장 끌어 놓고 원하는 순서로 이동하세요. 각 사진은 파일명(확장자 제외)을 "
                "Arial 10pt로 먼저 쓰고, 다음 줄에 높이 9.88cm로 삽입됩니다. 두 장마다 다음 페이지로 넘어갑니다."
            )
        elif selected is RawDataType.TWO_CUT_NON_COMMENT:
            self.picture_help.setText(
                "사진을 여러 장 끌어 놓고 원하는 순서로 이동하세요. 파일명 대신 빈 줄을 만든 뒤 "
                "높이 9.88cm로 삽입되며, 두 장마다 다음 페이지로 넘어갑니다."
            )
        else:
            self.picture_help.setText("HEPA Filter 형식에서는 첨부사진 목록을 사용하지 않습니다.")

    def selected_raw_data_type(self) -> RawDataType:
        """Return the currently selected Raw Data layout enum."""

        return RawDataType(self.raw_data_type.currentText())

    def current_request(self) -> RawDataDocumentRequest:
        """Build an immutable service request from the current form values."""

        return RawDataDocumentRequest(
            template_path=Path(self.template_input.path()),
            logo_path=Path(self.logo_input.path()),
            output_directory=Path(self.output_directory.path()),
            raw_data_type=self.selected_raw_data_type(),
            qualification_type=QualificationType(self.qualification_type.currentText()),
            document_number=self.document_number.text().strip(),
            hepa_filter_count=self.hepa_filter_count.value(),
            verification_name=self.verification_name.text().strip(),
            image_paths=self.image_list.paths(),
        )

    def generate_document(self) -> None:
        """Generate a Raw Data DOCX and offer to open the completed file."""

        request = self.current_request()
        errors = request.validation_errors()
        if errors:
            QMessageBox.warning(self, "생성 전 확인", "\n".join(dict.fromkeys(errors)))
            return
        self.generate_button.setEnabled(False)
        self.generate_button.setText("Word 생성 중...")
        self.status.setText("Word 생성 중...")
        QApplication.processEvents()
        try:
            output_path = self._generator.generate(request)
        except Exception as error:  # noqa: BLE001 - UI boundary reports service errors.
            self._context.services.resolve(logging.Logger).exception("Raw Data Word generation failed")
            self.status.setText("Raw Data 문서 생성에 실패했습니다.")
            QMessageBox.critical(self, "문서 생성 오류", str(error))
            return
        finally:
            self.generate_button.setEnabled(True)
            self.generate_button.setText("Raw Data Word 생성")
        self.status.setText(f"Raw Data 문서를 생성했습니다: {output_path}")
        answer = QMessageBox.question(
            self,
            "생성 완료",
            f"Raw Data Word 생성 완료!\n\n{output_path}\n\n파일을 바로 열까요?",
        )
        if answer == QMessageBox.StandardButton.Yes:
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(output_path)))


class RawDataGeneratorPlugin(Plugin):
    """Production Raw Data Generator plugin."""

    metadata = PluginMetadata(
        "raw-data",
        "Raw Data Generator",
        "Generate HEPA and ordered two-picture qualification Raw Data documents.",
        40,
    )

    def create_widget(self, context: ApplicationContext) -> QWidget:
        return RawDataGeneratorWidget(context)


def create_plugin() -> Plugin:
    """Return the Raw Data Generator plugin."""

    return RawDataGeneratorPlugin()
