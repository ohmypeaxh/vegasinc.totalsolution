"""Plugin contract for all application modules."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from PySide6.QtWidgets import QWidget

from vegas_doc.core.application_context import ApplicationContext


@dataclass(frozen=True, slots=True)
class PluginMetadata:
    """Descriptive metadata used by the plugin registry and navigation."""

    plugin_id: str
    name: str
    description: str
    order: int = 100


class Plugin(ABC):
    """Base interface implemented by every module page."""

    metadata: PluginMetadata

    @abstractmethod
    def create_widget(self, context: ApplicationContext) -> QWidget:
        """Create the plugin workspace widget without business behavior."""
