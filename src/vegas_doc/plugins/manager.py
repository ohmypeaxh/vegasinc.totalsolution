"""High-level plugin manager."""

from __future__ import annotations

import logging

from vegas_doc.plugins.loader import PluginLoadError, PluginLoader
from vegas_doc.plugins.plugin import Plugin
from vegas_doc.plugins.registry import PluginRegistry


class PluginManager:
    """Coordinate plugin loading and registry access."""

    def __init__(self, loader: PluginLoader, registry: PluginRegistry | None = None, logger: logging.Logger | None = None) -> None:
        self._loader = loader
        self._registry = registry or PluginRegistry()
        self._logger = logger
        self._load_errors: list[PluginLoadError] = []

    def load_installed(self) -> list[Plugin]:
        """Load plugins into the registry and return the ordered list."""

        result = self._loader.load()
        self._load_errors = list(result.errors)
        for plugin in result.plugins:
            try:
                self._registry.register(plugin)
            except ValueError as error:
                self._load_errors.append(PluginLoadError(plugin.metadata.plugin_id, str(error)))
                if self._logger is not None:
                    self._logger.exception("Failed to register plugin %s", plugin.metadata.plugin_id)
        return self._registry.all()

    @property
    def registry(self) -> PluginRegistry:
        """Return the plugin registry."""

        return self._registry

    @property
    def load_errors(self) -> tuple[PluginLoadError, ...]:
        """Return isolated plugin load or registration errors."""

        return tuple(self._load_errors)
