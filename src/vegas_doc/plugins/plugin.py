"""Plugin contract for all application modules."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from vegas_doc.core.application_context import ApplicationContext


class WorkspaceWidget(Protocol):
    """Structural type for QWidget-compatible plugin pages."""


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
    def create_widget(self, context: "ApplicationContext") -> WorkspaceWidget:
        """Create the plugin workspace widget without business behavior."""
