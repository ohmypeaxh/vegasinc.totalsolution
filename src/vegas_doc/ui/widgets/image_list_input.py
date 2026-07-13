"""Ordered multi-image picker with external drag-and-drop support."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QDragEnterEvent, QDragMoveEvent, QDropEvent
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFileDialog,
    QHBoxLayout,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff")


class ImagePathList(QListWidget):
    """List widget that accepts supported local image files."""

    paths_changed = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setDragEnabled(True)
        self.setDropIndicatorShown(True)
        self.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.setMinimumHeight(220)

    def paths(self) -> tuple[Path, ...]:
        """Return attached paths in the visible list order."""

        return tuple(Path(str(self.item(row).data(Qt.ItemDataRole.UserRole))) for row in range(self.count()))

    def set_paths(self, paths: tuple[Path, ...]) -> None:
        """Replace the current list with the supplied valid image paths."""

        self.clear()
        self.add_paths(paths)

    def add_paths(self, paths: tuple[Path, ...]) -> tuple[Path, ...]:
        """Append unique valid image paths and return rejected paths."""

        known = {str(path.resolve()).casefold() for path in self.paths()}
        rejected: list[Path] = []
        changed = False
        for path in paths:
            resolved = path.resolve()
            key = str(resolved).casefold()
            if not resolved.is_file() or resolved.suffix.lower() not in IMAGE_EXTENSIONS:
                rejected.append(path)
                continue
            if key in known:
                continue
            item = QListWidgetItem(resolved.name)
            item.setData(Qt.ItemDataRole.UserRole, str(resolved))
            item.setToolTip(str(resolved))
            self.addItem(item)
            known.add(key)
            changed = True
        if changed:
            self.paths_changed.emit()
        return tuple(rejected)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.source() is self:
            super().dragEnterEvent(event)
            return
        if self._supported_urls(event.mimeData().urls()):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event: QDragMoveEvent) -> None:
        if event.source() is self:
            super().dragMoveEvent(event)
        elif self._supported_urls(event.mimeData().urls()):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent) -> None:
        if event.source() is self:
            super().dropEvent(event)
            self.paths_changed.emit()
            return
        urls = event.mimeData().urls()
        if not self._supported_urls(urls):
            event.ignore()
            return
        rejected = self.add_paths(tuple(Path(url.toLocalFile()) for url in urls))
        if rejected:
            QMessageBox.warning(self, "지원하지 않는 사진", "일부 파일은 지원하는 이미지 형식이 아닙니다.")
        event.acceptProposedAction()

    @staticmethod
    def _supported_urls(urls) -> bool:  # type: ignore[no-untyped-def]
        return bool(urls) and all(
            url.isLocalFile() and Path(url.toLocalFile()).suffix.lower() in IMAGE_EXTENSIONS for url in urls
        )


class ImageListInput(QWidget):
    """Composite input for adding, deleting, and reordering many images."""

    paths_changed = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.list_widget = ImagePathList()
        self.list_widget.paths_changed.connect(self.paths_changed)

        add = QPushButton("사진 추가")
        remove = QPushButton("선택 삭제")
        move_up = QPushButton("위로")
        move_down = QPushButton("아래로")
        add.clicked.connect(self.browse)
        remove.clicked.connect(self.remove_selected)
        move_up.clicked.connect(lambda: self.move_current(-1))
        move_down.clicked.connect(lambda: self.move_current(1))

        buttons = QHBoxLayout()
        buttons.addWidget(add)
        buttons.addWidget(remove)
        buttons.addWidget(move_up)
        buttons.addWidget(move_down)
        buttons.addStretch()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        layout.addWidget(self.list_widget)
        layout.addLayout(buttons)

    def paths(self) -> tuple[Path, ...]:
        """Return selected images in generation order."""

        return self.list_widget.paths()

    def set_paths(self, paths: tuple[Path, ...]) -> None:
        """Replace the selected image list."""

        self.list_widget.set_paths(paths)

    def browse(self) -> None:
        """Select one or more images with the native file dialog."""

        selected, _ = QFileDialog.getOpenFileNames(
            self,
            "Raw Data 사진 선택",
            "",
            "Images (*.png *.jpg *.jpeg *.bmp *.tif *.tiff)",
        )
        if selected:
            self.list_widget.add_paths(tuple(Path(path) for path in selected))

    def remove_selected(self) -> None:
        """Remove all selected list entries."""

        rows = sorted((self.list_widget.row(item) for item in self.list_widget.selectedItems()), reverse=True)
        for row in rows:
            self.list_widget.takeItem(row)
        if rows:
            self.paths_changed.emit()

    def move_current(self, offset: int) -> None:
        """Move the current image one row while preserving its metadata."""

        row = self.list_widget.currentRow()
        destination = row + offset
        if row < 0 or destination < 0 or destination >= self.list_widget.count():
            return
        item = self.list_widget.takeItem(row)
        self.list_widget.insertItem(destination, item)
        self.list_widget.setCurrentRow(destination)
        self.paths_changed.emit()
