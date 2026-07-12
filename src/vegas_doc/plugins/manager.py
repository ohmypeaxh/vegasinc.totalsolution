"""High-level plugin manager."""

from __future__ import annotations

from vegas_doc.plugins.loader import PluginLoader
from vegas_doc.plugins.plugin import Plugin
from vegas_doc.plugins.registry import PluginRegistry


class PluginManager:
    """Coordinate plugin loading and registry access."""

    def __init__(self, loader: PluginLoader, registry: PluginRegistry | None = None) -> None:
        self._loader = loader
        self._registry = registry or PluginRegistry()

    def load_installed(self) -> list[Plugin]:
        """Load plugins into the registry and return the ordered list."""

        for plugin in self._loader.load():
            self._registry.register(plugin)
        return self._registry.all()

    @property
    def registry(self) -> PluginRegistry:
        """Return the plugin registry."""

        return self._registry
