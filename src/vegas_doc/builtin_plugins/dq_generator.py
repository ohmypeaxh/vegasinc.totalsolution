"""End-to-end DQ Generator plugin."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from PySide6.QtCore import QAbstractTableModel, QModelIndex, QObject, Qt, QThread, Signal
from PySide6.QtWidgets import QFileDialog, QFormLayout, QHBoxLayout, QLabel, QLineEdit, QMessageBox, QPushButton, QTableView, QTextEdit, QVBoxLayout, QWidget

from vegas_doc.core.application_context import ApplicationContext
from vegas_doc.core.config_manager import ConfigManager
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
        layout = QVBoxLayout(self)
        title = QLabel("DQ Generator")
        title.setObjectName("PageTitle")
        layout.addWidget(title)
        form = QFormLayout()
        self.project_name = QLineEdit()
        self.document_number = QLineEdit()
        self.source_path = QLineEdit()
        self.template_path = QLineEdit(str(Path("templates/default_dq_template.docx")))
        self.output_path = QLineEdit(str(Path("output/dq_output.docx")))
        form.addRow("Project", self.project_name)
        form.addRow("Document No.", self.document_number)
        form.addRow("URS/PDF/Image", self.source_path)
        form.addRow("Template", self.template_path)
        form.addRow("Output", self.output_path)
        layout.addLayout(form)
        buttons = QHBoxLayout()
        for text, slot in [("Import", self.import_file), ("Extract/Retry", self.start_extraction), ("Cancel", self.cancel), ("Save Project", self.save_project), ("Open Project", self.open_project), ("Generate", self.generate_docx)]:
            button = QPushButton(text)
            button.clicked.connect(slot)
            buttons.addWidget(button)
        buttons.addStretch()
        layout.addLayout(buttons)
        self.status = QLabel("대기 중")
        self.page_review = QTextEdit()
        self.page_review.setPlaceholderText("페이지 텍스트 검토/수정 영역")
        self.model = RequirementTableModel()
        self.table = QTableView()
        self.table.setModel(self.model)
        self.table.setSortingEnabled(True)
        layout.addWidget(self.status)
        layout.addWidget(self.page_review, 1)
        layout.addWidget(self.table, 3)

    def import_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "URS/PDF/Image 선택", "", "Documents (*.pdf *.png *.jpg *.jpeg *.tif *.tiff)")
        if path:
            self.source_path.setText(path)
            self._dirty = True

    def start_extraction(self) -> None:
        source = Path(self.source_path.text().strip())
        if not source.exists():
            QMessageBox.warning(self, "입력 확인", "가져올 URS/PDF/Image 파일을 선택해 주세요.")
            return
        self._thread = QThread()
        self._worker = DQExtractionWorker(source, self._context)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.progress.connect(lambda _value, message: self.status.setText(message))
        self._worker.completed.connect(self._on_extracted)
        self._worker.failed.connect(self._on_failed)
        self._thread.start()

    def cancel(self) -> None:
        if self._worker:
            self._worker.cancel()

    def _on_extracted(self, payload: tuple) -> None:
        self._extraction, requirements, responses, self._mappings = payload
        self.model.set_items(requirements, responses)
        if self._extraction and self._extraction.pages:
            self.page_review.setPlainText(self._extraction.pages[0].reviewed_text or self._extraction.pages[0].normalized_text or self._extraction.pages[0].original_text)
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
            mappings=tuple(self._mappings),
            template_settings=TemplateSettings(Path(self.template_path.text()), Path(self.output_path.text()).parent),
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
            self.model.set_items(project.requirements, {mapping.source_requirement_ids[0]: mapping.dq_response for mapping in project.mappings if mapping.dq_response and mapping.source_requirement_ids})
            self._extraction = project.extraction_results[0] if project.extraction_results else None
            self._mappings = project.mappings
            self.status.setText("프로젝트를 열었습니다.")

    def generate_docx(self) -> None:
        requirements = tuple(self.model.requirements)
        mappings = build_mappings(requirements, self.model.responses)
        template = Path(self.template_path.text())
        output = Path(self.output_path.text())
        errors = DQProjectValidator().validate_for_generation(self.project_name.text(), requirements, mappings, template, output)
        if errors:
            QMessageBox.warning(self, "생성 전 확인", "\n".join(errors))
            return
        self._generator.generate(template, output, {"project_name": self.project_name.text(), "document_number": self.document_number.text()}, requirements, mappings)
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
