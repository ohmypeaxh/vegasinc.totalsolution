"""File and directory path input with browse and drag-and-drop support."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Signal
from PySide6.QtGui import QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import QFileDialog, QHBoxLayout, QLineEdit, QMessageBox, QPushButton, QWidget


class FilePathInput(QWidget):
    """Validated path field supporting both browse dialogs and file drops."""

    path_changed = Signal(str)

    def __init__(
        self,
        *,
        mode: str = "file",
        extensions: tuple[str, ...] = (),
        dialog_filter: str = "All files (*)",
        drop_text: str = "",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        if mode not in {"file", "directory"}:
            raise ValueError("mode must be 'file' or 'directory'")
        self._mode = mode
        self._extensions = tuple(item.lower() for item in extensions)
        self._dialog_filter = dialog_filter
        self.line_edit = QLineEdit()
        self.line_edit.setPlaceholderText(drop_text)
        self.line_edit.textChanged.connect(self.path_changed)
        browse = QPushButton("[...]")
        browse.setFixedWidth(48)
        browse.clicked.connect(self.browse)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.line_edit, 1)
        layout.addWidget(browse)
        self.setAcceptDrops(True)

    def path(self) -> str:
        return self.line_edit.text().strip()

    def set_path(self, value: str | Path) -> None:
        self.line_edit.setText(str(value))

    def accepts(self, path: Path) -> bool:
        if self._mode == "directory":
            return path.is_dir()
        return path.is_file() and (not self._extensions or path.suffix.lower() in self._extensions)

    def browse(self) -> None:
        if self._mode == "directory":
            selected = QFileDialog.getExistingDirectory(self, "저장 폴더 선택")
        else:
            selected, _ = QFileDialog.getOpenFileName(self, "파일 선택", "", self._dialog_filter)
        if selected:
            self.set_path(selected)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        urls = event.mimeData().urls()
        if len(urls) == 1 and urls[0].isLocalFile() and self.accepts(Path(urls[0].toLocalFile())):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent) -> None:
        urls = event.mimeData().urls()
        if len(urls) != 1 or not urls[0].isLocalFile():
            event.ignore()
            return
        path = Path(urls[0].toLocalFile())
        if not self.accepts(path):
            allowed = ", ".join(self._extensions) if self._extensions else "폴더"
            QMessageBox.warning(self, "지원하지 않는 형식", f"허용 형식: {allowed}")
            event.ignore()
            return
        self.set_path(path)
        event.acceptProposedAction()
