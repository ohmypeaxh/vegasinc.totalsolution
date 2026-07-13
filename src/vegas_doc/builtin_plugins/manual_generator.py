"""PySide6 Manual Generator integrated from Word Maker v9."""

from __future__ import annotations

import logging
from datetime import date
from pathlib import Path

from PySide6.QtCore import QDate, QUrl
from PySide6.QtGui import QDesktopServices, QIntValidator
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDateEdit,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
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
from vegas_doc.models.manual_document import EQUIPMENT_SPECS, IMAGE_LABELS, InstrumentCounts, ManualDocumentRequest
from vegas_doc.plugins.plugin import Plugin, PluginMetadata
from vegas_doc.services.manual_generator import ManualDocumentGenerator
from vegas_doc.ui.widgets.file_path_input import FilePathInput


class ManualGeneratorWidget(QWidget):
    """Equipment manual form preserving the Word Maker v9 workflow."""

    def __init__(self, context: ApplicationContext) -> None:
        super().__init__()
        self._context = context
        self._generator = ManualDocumentGenerator()
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(8)
        eyebrow = QLabel("DOCUMENT AUTOMATION")
        eyebrow.setObjectName("Eyebrow")
        title = QLabel("Manual Generator")
        title.setObjectName("PageTitle")
        subtitle = QLabel("장비 화면과 알람 구성을 Word 템플릿에 반영해 표준 매뉴얼을 생성합니다.")
        subtitle.setObjectName("PageSubtitle")
        root.addWidget(eyebrow)
        root.addWidget(title)
        root.addWidget(subtitle)
        root.addSpacing(12)

        scroll = QScrollArea()
        scroll.setObjectName("WorkspaceScroll")
        scroll.setWidgetResizable(True)
        content = QWidget()
        content_layout = QVBoxLayout(content)

        project_group = QGroupBox("A. 문서 정보")
        project_form = QFormLayout(project_group)
        self.equipment = QComboBox()
        self.equipment.addItems([item.name for item in EQUIPMENT_SPECS])
        self.write_date = QDateEdit(QDate.currentDate())
        self.write_date.setCalendarPopup(True)
        self.write_date.setDisplayFormat("yyyy-MM-dd")
        self.document_suffix = QLineEdit()
        self.document_suffix.setValidator(QIntValidator(0, 99999, self))
        self.document_suffix.setPlaceholderText("블로워 또는 팬 개수")
        self.document_preview = QLabel()
        self.document_preview.setObjectName("DocumentPreview")
        self.equipment.currentTextChanged.connect(self._update_document_preview)
        self.document_suffix.textChanged.connect(self._update_document_preview)
        project_form.addRow("장비명 *", self.equipment)
        project_form.addRow("작성일 *", self.write_date)
        project_form.addRow("문서번호 수량 *", self.document_suffix)
        project_form.addRow("문서번호", self.document_preview)
        content_layout.addWidget(project_group)

        files_group = QGroupBox("B. 템플릿 및 화면 이미지")
        files_form = QFormLayout(files_group)
        self.template_input = FilePathInput(
            extensions=(".docx",),
            dialog_filter="Word template (*.docx)",
            drop_text="Word DOCX 템플릿을 끌어 놓으세요.",
        )
        files_form.addRow("삽입 Word 파일 *", self.template_input)
        self.image_inputs: list[FilePathInput] = []
        for label in IMAGE_LABELS:
            image_input = FilePathInput(
                extensions=(".png", ".jpg", ".jpeg", ".bmp"),
                dialog_filter="Image files (*.png *.jpg *.jpeg *.bmp)",
                drop_text=f"{label} 이미지를 끌어 놓으세요.",
            )
            self.image_inputs.append(image_input)
            files_form.addRow(f"{label} *" if label != "Alarm Setting" else label, image_input)
        self.use_alarm_setting = QCheckBox("Alarm Setting 화면 사용")
        self.use_alarm_setting.setChecked(True)
        self.use_alarm_setting.toggled.connect(self._toggle_alarm_setting)
        files_form.addRow("", self.use_alarm_setting)
        content_layout.addWidget(files_group)

        instruments_group = QGroupBox("C. 계측기 알람")
        instruments_layout = QVBoxLayout(instruments_group)
        self.use_instruments = QCheckBox("계측기 High / Low 알람 포함")
        self.use_instruments.toggled.connect(self._toggle_instruments)
        instruments_layout.addWidget(self.use_instruments)
        counts = QGridLayout()
        self.instrument_inputs: dict[str, QSpinBox] = {}
        for column, (key, label) in enumerate(
            (
                ("temperature", "온도"),
                ("humidity", "습도"),
                ("differential_pressure", "차압"),
                ("air_velocity", "풍속"),
            )
        ):
            caption = QLabel(label)
            value = QSpinBox()
            value.setRange(0, 999)
            value.setSuffix(" 개")
            counts.addWidget(caption, 0, column)
            counts.addWidget(value, 1, column)
            self.instrument_inputs[key] = value
        instruments_layout.addLayout(counts)
        content_layout.addWidget(instruments_group)

        output_group = QGroupBox("D. 출력")
        output_form = QFormLayout(output_group)
        self.output_directory = FilePathInput(mode="directory", drop_text="Word 저장 폴더를 선택하세요.")
        output_form.addRow("Word 저장 위치 *", self.output_directory)
        content_layout.addWidget(output_group)

        actions = QHBoxLayout()
        reset = QPushButton("입력값 초기화")
        reset.clicked.connect(self.reset_inputs)
        self.generate_button = QPushButton("Word 매뉴얼 생성")
        self.generate_button.setObjectName("PrimaryAction")
        self.generate_button.clicked.connect(self.generate_manual)
        actions.addStretch()
        actions.addWidget(reset)
        actions.addWidget(self.generate_button)
        content_layout.addLayout(actions)
        self.status = QLabel("템플릿 자리표시자: [##장비명##], [##문서번호##], [##작성일##], [##제품선택##], [##사진1##]~[##사진4##], [##알람리스트##]")
        self.status.setObjectName("MutedText")
        self.status.setWordWrap(True)
        content_layout.addWidget(self.status)
        content_layout.addStretch()
        scroll.setWidget(content)
        root.addWidget(scroll)

        self._toggle_alarm_setting(True)
        self._toggle_instruments(False)
        self._update_document_preview()

    def current_request(self) -> ManualDocumentRequest:
        """Collect the current UI state into an immutable service request."""

        counts = InstrumentCounts(
            temperature=self.instrument_inputs["temperature"].value(),
            humidity=self.instrument_inputs["humidity"].value(),
            differential_pressure=self.instrument_inputs["differential_pressure"].value(),
            air_velocity=self.instrument_inputs["air_velocity"].value(),
        )
        selected_date: date = self.write_date.date().toPython()
        return ManualDocumentRequest(
            template_path=Path(self.template_input.path()),
            output_directory=Path(self.output_directory.path()),
            equipment=self.equipment.currentText().strip(),
            document_suffix=self.document_suffix.text().strip(),
            write_date=selected_date,
            image_paths=tuple(Path(item.path()) for item in self.image_inputs),
            use_alarm_setting=self.use_alarm_setting.isChecked(),
            use_instruments=self.use_instruments.isChecked(),
            instrument_counts=counts,
        )

    def generate_manual(self) -> None:
        """Validate inputs, generate the Word file, and optionally open it."""

        request = self.current_request()
        errors = request.validation_errors()
        if errors:
            QMessageBox.warning(self, "입력 확인", "\n".join(dict.fromkeys(errors)))
            return
        self.generate_button.setEnabled(False)
        self.generate_button.setText("Word 생성 중...")
        self.status.setText("Word 생성 중...")
        QApplication.processEvents()
        try:
            output_path = self._generator.generate(request)
        except Exception as error:  # noqa: BLE001 - UI boundary reports service errors.
            self._context.services.resolve(logging.Logger).exception("Manual Word generation failed")
            self.status.setText("Word 매뉴얼 생성에 실패했습니다.")
            QMessageBox.critical(self, "문서 생성 오류", str(error))
            return
        finally:
            self.generate_button.setEnabled(True)
            self.generate_button.setText("Word 매뉴얼 생성")
        self.status.setText(f"Word 매뉴얼을 생성했습니다: {output_path}")
        answer = QMessageBox.question(self, "생성 완료", f"Word 생성 완료!\n\n{output_path}\n\n파일을 바로 열까요?")
        if answer == QMessageBox.Yes:
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(output_path)))

    def reset_inputs(self) -> None:
        """Return the form to the Word Maker v9 defaults."""

        self.equipment.setCurrentIndex(0)
        self.write_date.setDate(QDate.currentDate())
        self.document_suffix.clear()
        self.template_input.set_path("")
        self.output_directory.set_path("")
        for item in self.image_inputs:
            item.set_path("")
        self.use_alarm_setting.setChecked(True)
        self.use_instruments.setChecked(False)
        for item in self.instrument_inputs.values():
            item.setValue(0)
        self.status.setText("입력값을 초기화했습니다.")

    def _toggle_alarm_setting(self, enabled: bool) -> None:
        self.image_inputs[3].setEnabled(enabled)

    def _toggle_instruments(self, enabled: bool) -> None:
        for item in self.instrument_inputs.values():
            item.setEnabled(enabled)

    def _update_document_preview(self) -> None:
        spec = next((item for item in EQUIPMENT_SPECS if item.name == self.equipment.currentText()), None)
        code = spec.code if spec is not None else ""
        self.document_preview.setText(f"GR-OM-{code}{self.document_suffix.text().strip()}")


class ManualGeneratorPlugin(Plugin):
    """Production Manual Generator plugin."""

    metadata = PluginMetadata(
        plugin_id="manual",
        name="Manual Generator",
        description="Generate equipment manuals from Vegas Word templates and reviewed screenshots.",
        order=10,
    )

    def create_widget(self, context: ApplicationContext) -> QWidget:
        return ManualGeneratorWidget(context)


def create_plugin() -> Plugin:
    """Return the Manual Generator plugin."""

    return ManualGeneratorPlugin()
