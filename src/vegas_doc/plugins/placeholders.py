"""Reusable placeholder plugin implementations."""

from __future__ import annotations

from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

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
        title = QLabel(self.metadata.name)
        title.setObjectName("PageTitle")
        description = QLabel(self.metadata.description)
        description.setWordWrap(True)
        note = QLabel("Placeholder only. Business automation behavior is intentionally not implemented in this foundation.")
        note.setWordWrap(True)
        layout.addWidget(title)
        layout.addWidget(description)
        layout.addWidget(note)
        layout.addStretch()
        return widget
