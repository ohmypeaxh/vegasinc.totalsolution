"""End-to-end DQ Generator plugin."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from PySide6.QtCore import QAbstractTableModel, QDate, QModelIndex, QObject, Qt, QThread, Signal
from PySide6.QtWidgets import (QComboBox, QDateEdit, QFileDialog, QFormLayout, QGroupBox, QHBoxLayout, QLabel, QLineEdit, QMessageBox, QProgressBar, QPushButton, QScrollArea, QTableView, QTextEdit, QVBoxLayout, QWidget)

from vegas_doc.core.application_context import ApplicationContext
from vegas_doc.core.config_manager import ConfigManager
from vegas_doc.models.dq_document_data import DQDocumentData
from vegas_doc.models.dq_mapping import DQResponse
from vegas_doc.models.extraction import ExtractionPolicy
from vegas_doc.models.project import DQProject, PROJECT_SCHEMA_VERSION, ProjectInfo, TemplateSettings
from vegas_doc.models.urs import URSRequirement
from vegas_doc.plugins.plugin import Plugin, PluginMetadata
from vegas_doc.services.clova_ocr import ClovaOCRProvider, ClovaOCRSettings
from vegas_doc.services.document_extraction import PyMuPDFDocumentTextExtractor
from vegas_doc.services.docx_generator import DQDocxGenerator
from vegas_doc.services.dq_processing import DQProjectValidator, DQSuggestionService, DefaultURSParser, KeywordRequirementClassifier, build_mappings
from vegas_doc.services.ocr import ProviderOCRService
from vegas_doc.services.project_persistence import DQProjectRepository
from vegas_doc.services.secrets import KeyringSecretStore
from vegas_doc.ui.widgets.file_path_input import FilePathInput


class DQExtractionWorker(QObject):
    """Background extraction/parser worker that communicates only through signals."""

    progress = Signal(int, str)
    completed = Signal(tuple)
    failed = Signal(str)

    def __init__(self, source_path: Path, context: ApplicationContext) -> None:
        super().__init__()
        self._source_path = source_path
        self._context = context
        self._cancelled = False

    def cancel(self) -> None:
        self._cancelled = True

    def run(self) -> None:
        try:
            config = self._context.services.resolve(ConfigManager).load()
            provider = ClovaOCRProvider(ClovaOCRSettings.from_config(config), KeyringSecretStore())
            ocr_service = ProviderOCRService(provider)
            extractor = PyMuPDFDocumentTextExtractor(ocr_service)
            self.progress.emit(10, "문서 추출 중...")
            extraction = extractor.extract(self._source_path, _kind_for_path(self._source_path), ExtractionPolicy())
            if self._cancelled:
                self.failed.emit("작업이 취소되었습니다.")
                return
            self.progress.emit(60, "URS 요구사항 분석 중...")
            requirements = DefaultURSParser().parse(extraction)
            classifier = KeywordRequirementClassifier()
            suggester = DQSuggestionService()
            classified = tuple(replace(classifier.classify(item), user_reviewed=True) for item in requirements)
            responses = {item.requirement_id: suggester.suggest(item) for item in classified}
            mappings = build_mappings(classified, responses)
            self.progress.emit(100, "완료")
            self.completed.emit((extraction, classified, responses, mappings))
        except Exception as error:
            self.failed.emit(str(error))


class RequirementTableModel(QAbstractTableModel):
    """Editable requirement review table model."""

    HEADERS = ["Include", "Status", "ID", "Source", "Page", "Original", "Reviewed", "Category", "Section", "Response", "Verification", "Confidence", "Notes"]

    def __init__(self) -> None:
        super().__init__()
        self.requirements: list[URSRequirement] = []
        self.responses: dict[str, DQResponse] = {}

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self.requirements)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self.HEADERS)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole):  # type: ignore[no-untyped-def]
        if not index.isValid() or role not in {Qt.DisplayRole, Qt.EditRole, Qt.CheckStateRole}:
            return None
        req = self.requirements[index.row()]
        col = index.column()
        if col == 0 and role == Qt.CheckStateRole:
            return Qt.Checked if req.included else Qt.Unchecked
        values = [req.included, "Reviewed" if req.user_reviewed else "Needs Review", req.requirement_id, str(req.source_document), req.source_page, req.original_text, req.normalized_text, req.category or "", req.dq_section or "", self.responses.get(req.requirement_id).text if self.responses.get(req.requirement_id) else "", req.verification_method.value, req.confidence or "", req.user_notes or ""]
        return values[col]

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole):  # type: ignore[no-untyped-def]
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.HEADERS[section]
        return None

    def flags(self, index: QModelIndex) -> Qt.ItemFlag:
        flags = super().flags(index)
        if index.column() == 0:
            return flags | Qt.ItemIsUserCheckable | Qt.ItemIsEditable
        if index.column() in {6, 7, 8, 9, 12}:
            return flags | Qt.ItemIsEditable
        return flags

    def setData(self, index: QModelIndex, value, role: int = Qt.EditRole) -> bool:  # type: ignore[no-untyped-def]
        if not index.isValid():
            return False
        req = self.requirements[index.row()]
        col = index.column()
        if col == 0 and role == Qt.CheckStateRole:
            self.requirements[index.row()] = replace(req, included=value == Qt.Checked, user_reviewed=True)
        elif role == Qt.EditRole and col == 6:
            self.requirements[index.row()] = replace(req, normalized_text=str(value), user_reviewed=True)
        elif role == Qt.EditRole and col == 7:
            self.requirements[index.row()] = replace(req, category=str(value), user_reviewed=True)
        elif role == Qt.EditRole and col == 8:
            self.requirements[index.row()] = replace(req, dq_section=str(value), user_reviewed=True)
        elif role == Qt.EditRole and col == 9:
            self.responses[req.requirement_id] = DQResponse(f"RESP-{req.requirement_id}", str(value))
        elif role == Qt.EditRole and col == 12:
            self.requirements[index.row()] = replace(req, user_notes=str(value), user_reviewed=True)
        else:
            return False
        self.dataChanged.emit(index, index)
        return True

    def set_items(self, requirements: tuple[URSRequirement, ...], responses: dict[str, DQResponse]) -> None:
        self.beginResetModel()
        self.requirements = list(requirements)
        self.responses = dict(responses)
        self.endResetModel()


class DQGeneratorWidget(QWidget):
    """Responsive DQ Generator page with import, review, project, and generation actions."""

    def __init__(self, context: ApplicationContext) -> None:
        super().__init__()
        self._context = context
        self._repo = DQProjectRepository()
        self._generator = DQDocxGenerator()
        self._thread: QThread | None = None
        self._worker: DQExtractionWorker | None = None
        self._extraction = None
        self._mappings = tuple()
        self._dirty = False
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        title = QLabel("DQ Generator")
        title.setObjectName("PageTitle")
        root.addWidget(title)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        content_layout = QVBoxLayout(content)

        basic_group = QGroupBox("A. 기본 정보")
        basic_form = QFormLayout(basic_group)
        self.document_number = QLineEdit()
        self.version_number = QLineEdit("1.0")
        self.equipment_name = QLineEdit()
        self.project_name = self.equipment_name
        self.author_name = QLineEdit()
        self.author_date = QDateEdit(QDate.currentDate())
        self.author_date.setCalendarPopup(True)
        self.author_date.setDisplayFormat("yyyy-MM-dd")
        self.author_position = QComboBox()
        self.author_position.setEditable(True)
        self.author_position.addItems(["대표이사", "부장", "차장", "과장", "대리", "사원"])
        self.vendor_name = QLineEdit()
        for label, widget in (
            ("문서번호 *", self.document_number),
            ("버전번호 *", self.version_number),
            ("장비명 *", self.equipment_name),
            ("작성자 *", self.author_name),
            ("작성일 *", self.author_date),
            ("작성자 직위 *", self.author_position),
            ("업체명 *", self.vendor_name),
        ):
            basic_form.addRow(label, widget)
        content_layout.addWidget(basic_group)

        files_group = QGroupBox("B. 파일 첨부")
        files_form = QFormLayout(files_group)
        self.logo_input = FilePathInput(
            extensions=(".png", ".jpg", ".jpeg"),
            dialog_filter="Logo images (*.png *.jpg *.jpeg)",
            drop_text="로고 파일을 이곳에 끌어 놓으세요.",
        )
        self.template_input = FilePathInput(
            extensions=(".docx",),
            dialog_filter="Word template (*.docx)",
            drop_text="Word 템플릿을 이곳에 끌어 놓으세요.",
        )
        self.urs_input = FilePathInput(
            extensions=(".pdf",),
            dialog_filter="URS PDF (*.pdf)",
            drop_text="URS PDF 파일을 이곳에 끌어 놓으세요.",
        )
        self.logo_path = self.logo_input.line_edit
        self.template_path = self.template_input.line_edit
        self.source_path = self.urs_input.line_edit
        files_form.addRow("회사 로고 *", self.logo_input)
        files_form.addRow("Word 템플릿 *", self.template_input)
        files_form.addRow("URS PDF *", self.urs_input)
        content_layout.addWidget(files_group)

        range_group = QGroupBox("C. URS 추출 범위")
        range_form = QFormLayout(range_group)
        self.start_requirement = QLineEdit("6.4")
        self.end_requirement = QLineEdit("6.8")
        range_form.addRow("시작 요구사항 번호 *", self.start_requirement)
        range_form.addRow("종료 요구사항 번호 *", self.end_requirement)
        analyze = QPushButton("URS 분석")
        analyze.clicked.connect(self.start_extraction)
        range_form.addRow("", analyze)
        content_layout.addWidget(range_group)

        review_group = QGroupBox("D. OCR 결과 미리보기")
        review_layout = QVBoxLayout(review_group)
        self.page_review = QTextEdit()
        self.page_review.setPlaceholderText("PDF/OCR 원문 검토 및 수정 영역")
        self.model = RequirementTableModel()
        self.table = QTableView()
        self.table.setModel(self.model)
        self.table.setSortingEnabled(True)
        review_layout.addWidget(self.page_review)
        review_layout.addWidget(self.table)
        content_layout.addWidget(review_group)

        output_group = QGroupBox("E. 출력 설정")
        output_form = QFormLayout(output_group)
        self.output_directory_input = FilePathInput(mode="directory", drop_text="결과 저장 폴더")
        self.output_directory_input.set_path(Path("output"))
        self.output_path = self.output_directory_input.line_edit
        self.output_filename = QLineEdit()
        self.output_filename.setPlaceholderText("미입력 시 문서번호_장비명_DQ_작성일.docx")
        output_form.addRow("저장 위치 *", self.output_directory_input)
        output_form.addRow("결과 파일명", self.output_filename)
        content_layout.addWidget(output_group)

        action_row = QHBoxLayout()
        for text, slot in (
            ("OCR 결과 검토", lambda: self.table.setFocus()),
            ("Save Project", self.save_project),
            ("Open Project", self.open_project),
            ("입력값 초기화", self.reset_inputs),
            ("작업 취소", self.cancel),
        ):
            button = QPushButton(text)
            button.clicked.connect(slot)
            action_row.addWidget(button)
        generate = QPushButton("Word 문서 생성")
        generate.setObjectName("PrimaryAction")
        generate.clicked.connect(self.generate_docx)
        action_row.addWidget(generate)
        content_layout.addLayout(action_row)

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.status = QLabel("대기 중")
        content_layout.addWidget(self.progress)
        content_layout.addWidget(self.status)
        content_layout.addStretch()
        scroll.setWidget(content)
        root.addWidget(scroll)

    def current_document_data(self) -> DQDocumentData:
        return DQDocumentData(
            logo_path=Path(self.logo_path.text().strip()),
            template_path=Path(self.template_path.text().strip()),
            urs_pdf_path=Path(self.source_path.text().strip()),
            document_number=self.document_number.text().strip(),
            version_number=self.version_number.text().strip(),
            equipment_name=self.equipment_name.text().strip(),
            author_name=self.author_name.text().strip(),
            author_date=self.author_date.date().toPython(),
            author_position=self.author_position.currentText().strip(),
            vendor_name=self.vendor_name.text().strip(),
            start_requirement=self.start_requirement.text().strip(),
            end_requirement=self.end_requirement.text().strip(),
            output_directory=Path(self.output_directory_input.path()),
            output_filename=self.output_filename.text().strip(),
        )

    def reset_inputs(self) -> None:
        for field in (self.document_number, self.equipment_name, self.author_name, self.vendor_name, self.logo_path, self.template_path, self.source_path, self.output_filename):
            field.clear()
        self.version_number.setText("1.0")
        self.author_date.setDate(QDate.currentDate())
        self.start_requirement.setText("6.4")
        self.end_requirement.setText("6.8")
        self.model.set_items((), {})
        self.page_review.clear()
        self.progress.setValue(0)
        self.status.setText("입력값을 초기화했습니다.")
        self._dirty = False

    def import_file(self) -> None:
        self.urs_input.browse()
        self._dirty = bool(self.source_path.text().strip())

    def start_extraction(self) -> None:
        data = self.current_document_data()
        range_errors = [error for error in data.validation_errors(require_existing_files=False) if "요구사항 번호" in error]
        source = data.urs_pdf_path
        if source.suffix.lower() != ".pdf" or not source.is_file():
            range_errors.append("유효한 URS PDF 파일을 선택해 주세요.")
        if range_errors:
            QMessageBox.warning(self, "입력 확인", "\n".join(dict.fromkeys(range_errors)))
            return
        self._thread = QThread()
        self._worker = DQExtractionWorker(source, self._context)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.progress.connect(self._on_progress)
        self._worker.completed.connect(self._on_extracted)
        self._worker.failed.connect(self._on_failed)
        self._thread.start()

    def cancel(self) -> None:
        if self._worker:
            self._worker.cancel()

    def _on_progress(self, value: int, message: str) -> None:
        self.progress.setValue(value)
        self.status.setText(message)

    def _on_extracted(self, payload: tuple) -> None:
        self._extraction, requirements, responses, self._mappings = payload
        self.model.set_items(requirements, responses)
        if self._extraction and self._extraction.pages:
            self.page_review.setPlainText(self._extraction.pages[0].reviewed_text or self._extraction.pages[0].normalized_text or self._extraction.pages[0].original_text)
        self.progress.setValue(100)
        self.status.setText("추출 및 분석이 완료되었습니다.")
        self._dirty = True
        self._stop_thread()

    def _on_failed(self, message: str) -> None:
        self.status.setText(f"오류: {message}")
        self._stop_thread()

    def _stop_thread(self) -> None:
        if self._thread:
            self._thread.quit()
            self._thread.wait(1000)
        self._thread = None
        self._worker = None

    def current_project(self) -> DQProject:
        return DQProject(
            PROJECT_SCHEMA_VERSION,
            ProjectInfo(self.document_number.text().strip() or "DQ-PROJECT", self.project_name.text().strip() or "DQ Project"),
            source_references=(Path(self.source_path.text()),) if self.source_path.text().strip() else (),
            extraction_results=(self._extraction,) if self._extraction else (),
            requirements=tuple(self.model.requirements),
            corrections={
                "version_number": self.version_number.text().strip(),
                "author_name": self.author_name.text().strip(),
                "author_date": self.author_date.date().toString("yyyy-MM-dd"),
                "author_position": self.author_position.currentText().strip(),
                "vendor_name": self.vendor_name.text().strip(),
                "logo_path": self.logo_path.text().strip(),
                "start_requirement": self.start_requirement.text().strip(),
                "end_requirement": self.end_requirement.text().strip(),
                "output_filename": self.output_filename.text().strip(),
            },
            mappings=tuple(self._mappings),
            template_settings=TemplateSettings(Path(self.template_path.text()), Path(self.output_directory_input.path())),
        )

    def save_project(self) -> None:
        path, _ = QFileDialog.getSaveFileName(self, "프로젝트 저장", "project.vdqproj", "Vegas DQ Project (*.vdqproj)")
        if path:
            self._repo.save(self.current_project(), Path(path), overwrite=True)
            self._dirty = False
            self.status.setText("프로젝트를 저장했습니다.")

    def open_project(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "프로젝트 열기", "", "Vegas DQ Project (*.vdqproj)")
        if path:
            project = self._repo.load(Path(path))
            self.project_name.setText(project.project_info.name)
            self.document_number.setText(project.project_info.project_id)
            if project.source_references:
                self.source_path.setText(str(project.source_references[0]))
            values = project.corrections
            self.version_number.setText(values.get("version_number", "1.0"))
            self.author_name.setText(values.get("author_name", ""))
            if values.get("author_date"):
                self.author_date.setDate(QDate.fromString(values["author_date"], "yyyy-MM-dd"))
            self.author_position.setCurrentText(values.get("author_position", ""))
            self.vendor_name.setText(values.get("vendor_name", ""))
            self.logo_path.setText(values.get("logo_path", ""))
            self.start_requirement.setText(values.get("start_requirement", "6.4"))
            self.end_requirement.setText(values.get("end_requirement", "6.8"))
            self.output_filename.setText(values.get("output_filename", ""))
            if project.template_settings.template_path:
                self.template_path.setText(str(project.template_settings.template_path))
            if project.template_settings.output_directory:
                self.output_directory_input.set_path(project.template_settings.output_directory)
            self.model.set_items(project.requirements, {mapping.source_requirement_ids[0]: mapping.dq_response for mapping in project.mappings if mapping.dq_response and mapping.source_requirement_ids})
            self._extraction = project.extraction_results[0] if project.extraction_results else None
            self._mappings = project.mappings
            self.status.setText("프로젝트를 열었습니다.")

    def generate_docx(self) -> None:
        data = self.current_document_data()
        requirements = tuple(self.model.requirements)
        mappings = build_mappings(requirements, self.model.responses)
        output = data.output_path()
        errors = data.validation_errors()
        errors.extend(DQProjectValidator().validate_for_generation(data.equipment_name, requirements, mappings, data.template_path, output))
        if errors:
            QMessageBox.warning(self, "생성 전 확인", "\n".join(dict.fromkeys(errors)))
            return
        context = {
            "project_name": data.equipment_name,
            "document_number": data.document_number,
            "version_number": data.version_number,
            "equipment_name": data.equipment_name,
            "author_name": data.author_name,
            "author_date": data.author_date.strftime("%Y-%m-%d"),
            "author_position": data.author_position,
            "vendor_name": data.vendor_name,
        }
        self.progress.setValue(80)
        self.status.setText("Word 문서 생성 중...")
        self._generator.generate(data.template_path, output, context, requirements, mappings)
        self.progress.setValue(100)
        self.status.setText(f"DQ 문서를 생성했습니다: {output}")
        self._dirty = False

    def closeEvent(self, event):  # type: ignore[no-untyped-def]
        if self._dirty:
            answer = QMessageBox.question(self, "저장 확인", "저장되지 않은 변경사항이 있습니다. 닫을까요?")
            if answer != QMessageBox.Yes:
                event.ignore()
                return
        event.accept()


class DQGeneratorPlugin(Plugin):
    """Real DQ Generator plugin."""

    metadata = PluginMetadata("dq", "DQ Generator", "Import URS, review requirements, and generate DQ documents.", 20)

    def create_widget(self, context: ApplicationContext) -> QWidget:
        return DQGeneratorWidget(context)


def create_plugin() -> Plugin:
    """Return the DQ Generator plugin."""

    return DQGeneratorPlugin()


def _kind_for_path(path: Path):  # type: ignore[no-untyped-def]
    from vegas_doc.models.extraction import DocumentKind

    return DocumentKind.IMAGE if path.suffix.lower() in {".png", ".jpg", ".jpeg", ".tif", ".tiff"} else DocumentKind.MIXED_PDF
