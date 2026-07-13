"""F&DS Generator with ranged URS OCR, review, rules, and Word output."""

from __future__ import annotations

import logging
from dataclasses import replace
from datetime import date
from pathlib import Path

from PySide6.QtCore import QDate, QObject, Qt, QThread, QUrl, Signal
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QAbstractItemView,
    QDateEdit,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from vegas_doc.core.application_context import ApplicationContext
from vegas_doc.core.config_manager import ConfigManager
from vegas_doc.models.dq_document_data import section_key
from vegas_doc.models.extraction import DocumentKind, ExtractionPolicy
from vegas_doc.models.fds_document import FDSDocumentRequest, FDSStatement, FDSTransformationRule
from vegas_doc.plugins.plugin import Plugin, PluginMetadata
from vegas_doc.services.clova_ocr import ClovaOCRProvider, ClovaOCRSettings
from vegas_doc.services.document_extraction import PyMuPDFDocumentTextExtractor, extraction_failure_message
from vegas_doc.services.fds_generator import (
    DEFAULT_FDS_TRANSFORMATION_RULES,
    FDSDocumentGenerator,
    FDSSentenceTransformer,
    FDSURSParser,
    transformation_rules_from_config,
    transformation_rules_to_config,
)
from vegas_doc.services.ocr import ProviderOCRService
from vegas_doc.services.secrets import KeyringSecretStore
from vegas_doc.ui.widgets.file_path_input import FilePathInput
from vegas_doc.utils.date_format import QT_DOCUMENT_DATE_FORMAT


class FDSExtractionWorker(QObject):
    """Extract and transform only the selected URS range off the UI thread."""

    progress = Signal(int, str)
    completed = Signal(tuple)
    failed = Signal(str)

    def __init__(
        self,
        source_path: Path,
        start_section: str,
        end_section: str,
        rules: tuple[FDSTransformationRule, ...],
        context: ApplicationContext,
    ) -> None:
        super().__init__()
        self._source_path = source_path
        self._start_section = start_section
        self._end_section = end_section
        self._rules = rules
        self._context = context

    def run(self) -> None:
        """Run embedded-text extraction with CLOVA OCR fallback and transform results."""

        try:
            values = self._context.services.resolve(ConfigManager).load()
            provider = ClovaOCRProvider(ClovaOCRSettings.from_config(values), KeyringSecretStore())
            extractor = PyMuPDFDocumentTextExtractor(ProviderOCRService(provider))
            self.progress.emit(10, "선택한 URS 범위를 읽고 있습니다...")
            extraction = extractor.extract_range(
                self._source_path,
                DocumentKind.MIXED_PDF,
                ExtractionPolicy(),
                self._start_section,
                self._end_section,
            )
            failure = extraction_failure_message(extraction)
            if failure is not None:
                raise RuntimeError(failure)
            self.progress.emit(70, "F&DS 문장 규칙을 적용하고 있습니다...")
            parsed = FDSURSParser().parse(extraction, self._start_section, self._end_section)
            transformer = FDSSentenceTransformer(self._rules)
            statements = tuple(replace(item, generated_text=transformer.transform(item.original_text)) for item in parsed)
            self.progress.emit(100, "URS 범위 분석을 완료했습니다.")
            self.completed.emit((extraction, statements))
        except Exception as error:  # noqa: BLE001 - worker boundary isolates extraction failure.
            self._context.services.resolve(logging.Logger).exception("F&DS URS extraction failed")
            self.failed.emit(f"URS 분석 중 오류가 발생했습니다: {error}")


class FDSGeneratorWidget(QWidget):
    """Real F&DS workflow and its editable sentence-rule tab."""

    def __init__(self, context: ApplicationContext) -> None:
        super().__init__()
        self._context = context
        self._config = context.services.resolve(ConfigManager)
        self._generator = FDSDocumentGenerator()
        self._thread: QThread | None = None
        self._worker: FDSExtractionWorker | None = None
        self._extraction = None
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(8)
        eyebrow = QLabel("FUNCTIONAL & DESIGN SPECIFICATION")
        eyebrow.setObjectName("Eyebrow")
        title = QLabel("F&DS Generator")
        title.setObjectName("PageTitle")
        subtitle = QLabel("선택한 URS 범위를 설계 문장으로 변환하고 검토한 뒤 Word 문서로 생성합니다.")
        subtitle.setObjectName("PageSubtitle")
        root.addWidget(eyebrow)
        root.addWidget(title)
        root.addWidget(subtitle)
        root.addSpacing(10)

        self.tabs = QTabWidget()
        self.tabs.setObjectName("WorkspaceTabs")
        self.tabs.addTab(self._build_generator_tab(), "F&DS Generator")
        self.tabs.addTab(self._build_rules_tab(), "F&DS Rules")
        root.addWidget(self.tabs, 1)

    def _build_generator_tab(self) -> QWidget:
        tab = QWidget()
        tab_layout = QVBoxLayout(tab)
        tab_layout.setContentsMargins(0, 12, 0, 0)
        scroll = QScrollArea()
        scroll.setObjectName("WorkspaceScroll")
        scroll.setWidgetResizable(True)
        content = QWidget()
        content_layout = QVBoxLayout(content)

        info_group = QGroupBox("A. 문서 정보")
        info_form = QFormLayout(info_group)
        self.equipment_name = QLineEdit()
        self.document_number = QLineEdit()
        self.logo_input = FilePathInput(
            extensions=(".png", ".jpg", ".jpeg", ".bmp"),
            dialog_filter="Logo images (*.png *.jpg *.jpeg *.bmp)",
            drop_text="회사 로고 이미지를 끌어 놓으세요.",
        )
        self.write_date = QDateEdit(QDate.currentDate())
        self.write_date.setCalendarPopup(True)
        self.write_date.setDisplayFormat(QT_DOCUMENT_DATE_FORMAT)
        info_form.addRow("장비명 *", self.equipment_name)
        info_form.addRow("문서번호 *", self.document_number)
        info_form.addRow("회사 로고 *", self.logo_input)
        info_form.addRow("작성일 *", self.write_date)
        content_layout.addWidget(info_group)

        urs_group = QGroupBox("B. URS 범위 OCR")
        urs_form = QFormLayout(urs_group)
        self.urs_input = FilePathInput(
            extensions=(".pdf",),
            dialog_filter="URS PDF (*.pdf)",
            drop_text="URS PDF를 끌어 놓으세요.",
        )
        self.start_requirement = QLineEdit("6.4")
        self.end_requirement = QLineEdit("6.8")
        analyze = QPushButton("선택 범위 URS 분석")
        analyze.clicked.connect(self.start_extraction)
        urs_form.addRow("URS PDF *", self.urs_input)
        urs_form.addRow("시작 요구사항 번호 *", self.start_requirement)
        urs_form.addRow("종료 요구사항 번호 *", self.end_requirement)
        urs_form.addRow("", analyze)
        content_layout.addWidget(urs_group)

        review_group = QGroupBox("C. F&DS 문장 검토")
        review_layout = QVBoxLayout(review_group)
        self.review_table = QTableWidget(0, 4)
        self.review_table.setHorizontalHeaderLabels(("URS 번호", "Page", "URS 원문", "F&DS 변환 내용"))
        self.review_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.review_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.review_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.review_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.review_table.setAlternatingRowColors(True)
        self.review_table.setMinimumHeight(480)
        review_group.setMinimumHeight(560)
        review_layout.addWidget(self.review_table)
        review_note = QLabel("F&DS 변환 내용 열은 Word 생성 전에 직접 수정할 수 있습니다. 번호는 5.2.1부터 자동 부여됩니다.")
        review_note.setObjectName("MutedText")
        review_layout.addWidget(review_note)
        content_layout.addWidget(review_group)

        output_group = QGroupBox("D. Word 출력")
        output_form = QFormLayout(output_group)
        self.template_input = FilePathInput(
            extensions=(".docx",),
            dialog_filter="Word template (*.docx)",
            drop_text="##F&DS내용##이 포함된 Word 템플릿을 끌어 놓으세요.",
        )
        self.output_directory = FilePathInput(mode="directory", drop_text="Word 저장 폴더를 선택하세요.")
        output_form.addRow("Word 템플릿 *", self.template_input)
        output_form.addRow("Word 저장 위치 *", self.output_directory)
        content_layout.addWidget(output_group)

        actions = QHBoxLayout()
        generate = QPushButton("F&DS 문서 생성")
        generate.setObjectName("PrimaryAction")
        generate.clicked.connect(self.generate_fds)
        actions.addStretch()
        actions.addWidget(generate)
        content_layout.addLayout(actions)
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.status = QLabel("대기 중")
        content_layout.addWidget(self.progress)
        content_layout.addWidget(self.status)
        content_layout.addStretch()
        scroll.setWidget(content)
        tab_layout.addWidget(scroll)
        return tab

    def _build_rules_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 22, 20, 20)
        title = QLabel("F&DS Sentence Rules")
        title.setObjectName("SectionTitle")
        description = QLabel(
            "URS 문장의 끝 표현이 일치하면 오른쪽 표현으로 교체합니다. 위쪽 규칙부터 적용되므로 더 구체적인 규칙을 먼저 두세요."
        )
        description.setObjectName("PageSubtitle")
        description.setWordWrap(True)
        layout.addWidget(title)
        layout.addWidget(description)
        layout.addSpacing(10)

        self.rules_table = QTableWidget(0, 2)
        self.rules_table.setHorizontalHeaderLabels(("URS 원문 끝 표현", "F&DS 변환 끝 표현"))
        self.rules_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.rules_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.rules_table.setAlternatingRowColors(True)
        layout.addWidget(self.rules_table, 1)

        buttons = QHBoxLayout()
        add = QPushButton("규칙 추가")
        remove = QPushButton("선택 규칙 삭제")
        move_up = QPushButton("위로")
        move_down = QPushButton("아래로")
        reset = QPushButton("기본 규칙 복원")
        save = QPushButton("규칙 저장")
        save.setObjectName("PrimaryAction")
        add.clicked.connect(self.add_rule)
        remove.clicked.connect(self.remove_selected_rules)
        move_up.clicked.connect(lambda: self.move_rule(-1))
        move_down.clicked.connect(lambda: self.move_rule(1))
        reset.clicked.connect(self.reset_rules)
        save.clicked.connect(self.save_rules)
        buttons.addWidget(add)
        buttons.addWidget(remove)
        buttons.addWidget(move_up)
        buttons.addWidget(move_down)
        buttons.addWidget(reset)
        buttons.addStretch()
        buttons.addWidget(save)
        layout.addLayout(buttons)
        self.rules_status = QLabel("규칙은 사용자 설정에 저장되며 다음 URS 분석부터 적용됩니다.")
        self.rules_status.setObjectName("MutedText")
        layout.addWidget(self.rules_status)
        self._populate_rules(transformation_rules_from_config(self._config.load().get("fds_transformation_rules")))
        return tab

    def current_rules(self) -> tuple[FDSTransformationRule, ...]:
        """Return validated rules in visible table order."""

        rules: list[FDSTransformationRule] = []
        for row in range(self.rules_table.rowCount()):
            source_item = self.rules_table.item(row, 0)
            target_item = self.rules_table.item(row, 1)
            source = source_item.text().strip() if source_item is not None else ""
            target = target_item.text().strip() if target_item is not None else ""
            if not source and not target:
                continue
            rules.append(FDSTransformationRule(source, target))
        if not rules:
            raise ValueError("최소 한 개의 F&DS 변환 규칙이 필요합니다.")
        return tuple(rules)

    def save_rules(self) -> None:
        """Persist edited rules as non-secret user configuration."""

        try:
            rules = self.current_rules()
        except ValueError as error:
            QMessageBox.warning(self, "규칙 확인", str(error))
            return
        values = self._config.load()
        values["fds_transformation_rules"] = transformation_rules_to_config(rules)
        self._config.save(values)
        self.rules_status.setText(f"F&DS 변환 규칙 {len(rules)}개를 저장했습니다.")

    def add_rule(self) -> None:
        row = self.rules_table.rowCount()
        self.rules_table.insertRow(row)
        self.rules_table.setItem(row, 0, QTableWidgetItem(""))
        self.rules_table.setItem(row, 1, QTableWidgetItem(""))
        self.rules_table.setCurrentCell(row, 0)

    def remove_selected_rules(self) -> None:
        for row in sorted({index.row() for index in self.rules_table.selectedIndexes()}, reverse=True):
            self.rules_table.removeRow(row)

    def move_rule(self, offset: int) -> None:
        """Move the selected rule to change first-match priority."""

        row = self.rules_table.currentRow()
        target = row + offset
        if row < 0 or target < 0 or target >= self.rules_table.rowCount():
            return
        values = [self.rules_table.item(row, column).text() for column in range(2)]
        self.rules_table.removeRow(row)
        self.rules_table.insertRow(target)
        for column, value in enumerate(values):
            self.rules_table.setItem(target, column, QTableWidgetItem(value))
        self.rules_table.setCurrentCell(target, 0)

    def reset_rules(self) -> None:
        self._populate_rules(DEFAULT_FDS_TRANSFORMATION_RULES)
        self.rules_status.setText("기본 규칙을 불러왔습니다. 저장 버튼을 누르면 적용됩니다.")

    def _populate_rules(self, rules: tuple[FDSTransformationRule, ...]) -> None:
        self.rules_table.setRowCount(len(rules))
        for row, rule in enumerate(rules):
            self.rules_table.setItem(row, 0, QTableWidgetItem(rule.source_ending))
            self.rules_table.setItem(row, 1, QTableWidgetItem(rule.target_ending))

    def start_extraction(self) -> None:
        """Validate the source and start ranged OCR/extraction in a worker thread."""

        if self._thread is not None and self._thread.isRunning():
            QMessageBox.information(self, "작업 진행 중", "이미 URS 분석이 진행 중입니다.")
            return
        source = Path(self.urs_input.path())
        errors: list[str] = []
        if source.suffix.lower() != ".pdf" or not source.is_file():
            errors.append("유효한 URS PDF 파일을 선택해 주세요.")
        try:
            if section_key(self.start_requirement.text()) > section_key(self.end_requirement.text()):
                errors.append("시작 요구사항 번호는 종료 번호보다 클 수 없습니다.")
        except ValueError:
            errors.append("시작 및 종료 요구사항 번호를 숫자 계층 형식으로 입력해 주세요. 예: 6.4")
        try:
            rules = self.current_rules()
        except ValueError as error:
            errors.append(str(error))
            rules = ()
        if errors:
            QMessageBox.warning(self, "입력 확인", "\n".join(dict.fromkeys(errors)))
            return
        self._thread = QThread()
        self._worker = FDSExtractionWorker(
            source,
            self.start_requirement.text().strip(),
            self.end_requirement.text().strip(),
            rules,
            self._context,
        )
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.progress.connect(self._on_progress)
        self._worker.completed.connect(self._on_extracted)
        self._worker.failed.connect(self._on_failed)
        self._worker.completed.connect(self._worker.deleteLater)
        self._worker.failed.connect(self._worker.deleteLater)
        self.progress.setValue(0)
        self._thread.start()

    def _on_progress(self, value: int, message: str) -> None:
        self.progress.setValue(value)
        self.status.setText(message)

    def _on_extracted(self, payload: tuple) -> None:
        self._extraction, statements = payload
        self._populate_review(statements)
        self.progress.setValue(100)
        if statements:
            self.status.setText(f"선택 범위에서 {len(statements)}개의 URS 문장을 변환했습니다.")
        else:
            self.status.setText("선택 범위에서 요구사항 문장을 찾지 못했습니다.")
            QMessageBox.warning(self, "분석 결과", "선택 범위와 URS 번호 형식을 확인해 주세요.")
        self._stop_thread()

    def _on_failed(self, message: str) -> None:
        self.status.setText(message)
        QMessageBox.warning(self, "URS 분석 오류", message)
        self._stop_thread()

    def _stop_thread(self) -> None:
        if self._thread is not None:
            self._thread.quit()
            self._thread.wait(1000)
            self._thread.deleteLater()
        self._thread = None
        self._worker = None

    def _populate_review(self, statements: tuple[FDSStatement, ...]) -> None:
        self.review_table.setRowCount(len(statements))
        for row, statement in enumerate(statements):
            values = (statement.requirement_id, str(statement.source_page), statement.original_text, statement.generated_text)
            for column, value in enumerate(values):
                item = QTableWidgetItem(value)
                if column < 3:
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self.review_table.setItem(row, column, item)
        self.review_table.resizeRowsToContents()

    def current_statements(self) -> tuple[FDSStatement, ...]:
        statements: list[FDSStatement] = []
        for row in range(self.review_table.rowCount()):
            statements.append(
                FDSStatement(
                    requirement_id=self.review_table.item(row, 0).text(),
                    source_page=int(self.review_table.item(row, 1).text()),
                    original_text=self.review_table.item(row, 2).text(),
                    generated_text=self.review_table.item(row, 3).text(),
                )
            )
        return tuple(statements)

    def current_request(self) -> FDSDocumentRequest:
        selected_date: date = self.write_date.date().toPython()
        return FDSDocumentRequest(
            template_path=Path(self.template_input.path()),
            source_pdf_path=Path(self.urs_input.path()),
            logo_path=Path(self.logo_input.path()),
            output_directory=Path(self.output_directory.path()),
            equipment_name=self.equipment_name.text().strip(),
            document_number=self.document_number.text().strip(),
            write_date=selected_date,
            start_requirement=self.start_requirement.text().strip(),
            end_requirement=self.end_requirement.text().strip(),
            statements=self.current_statements(),
        )

    def generate_fds(self) -> None:
        """Generate the reviewed F&DS Word document and optionally open it."""

        request = self.current_request()
        errors = request.validation_errors()
        if errors:
            QMessageBox.warning(self, "생성 전 확인", "\n".join(dict.fromkeys(errors)))
            return
        self.status.setText("F&DS Word 문서를 생성하고 있습니다...")
        try:
            output_path = self._generator.generate(request)
        except Exception as error:  # noqa: BLE001 - UI boundary reports service errors.
            self._context.services.resolve(logging.Logger).exception("F&DS Word generation failed")
            self.status.setText("F&DS 문서 생성에 실패했습니다.")
            QMessageBox.critical(self, "문서 생성 오류", str(error))
            return
        self.status.setText(f"F&DS 문서를 생성했습니다: {output_path}")
        answer = QMessageBox.question(self, "생성 완료", f"F&DS Word 생성 완료!\n\n{output_path}\n\n파일을 바로 열까요?")
        if answer == QMessageBox.Yes:
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(output_path)))


class FDSGeneratorPlugin(Plugin):
    """Production F&DS Generator plugin."""

    metadata = PluginMetadata("fds", "F&DS Generator", "Transform a selected URS range into reviewed F&DS content.", 30)

    def create_widget(self, context: ApplicationContext) -> QWidget:
        return FDSGeneratorWidget(context)


def create_plugin() -> Plugin:
    """Return the F&DS Generator plugin."""

    return FDSGeneratorPlugin()
