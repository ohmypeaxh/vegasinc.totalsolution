"""Reusable placeholder plugin implementations."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout, QWidget

from vegas_doc.core.application_context import ApplicationContext
from vegas_doc.plugins.plugin import Plugin, PluginMetadata


class PlaceholderPlugin(Plugin):
    """A production-safe placeholder module with no business logic."""

    def __init__(self, metadata: PluginMetadata) -> None:
        self.metadata = metadata

    def create_widget(self, context: ApplicationContext) -> QWidget:
        """Create a placeholder page for future module implementation."""

        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(42, 36, 42, 36)
        eyebrow = QLabel("VEGAS WORKSPACE")
        eyebrow.setObjectName("Eyebrow")
        title = QLabel(self.metadata.name)
        title.setObjectName("PageTitle")
        description = QLabel(self.metadata.description)
        description.setObjectName("PageSubtitle")
        description.setWordWrap(True)
        card = QFrame()
        card.setObjectName("EmptyStateCard")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(36, 34, 36, 34)
        status = QLabel("FOUNDATION READY")
        status.setObjectName("StatusBadge")
        status.setAlignment(Qt.AlignCenter)
        status.setFixedWidth(154)
        heading = QLabel("모듈 작업 공간이 준비되어 있습니다.")
        heading.setObjectName("EmptyStateTitle")
        note = QLabel("기능 요구사항이 확정되면 플러그인 내부에 독립적으로 구현됩니다.")
        note.setObjectName("MutedText")
        note.setWordWrap(True)
        card_layout.addWidget(status)
        card_layout.addSpacing(12)
        card_layout.addWidget(heading)
        card_layout.addWidget(note)
        card_layout.addStretch()
        layout.addWidget(eyebrow)
        layout.addWidget(title)
        layout.addWidget(description)
        layout.addSpacing(22)
        layout.addWidget(card, 1)
        layout.addStretch()
        return widget
