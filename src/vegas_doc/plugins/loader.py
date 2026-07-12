"""Plugin discovery and loading."""

from __future__ import annotations

import importlib
import logging
import pkgutil
from dataclasses import dataclass
from pathlib import Path

from vegas_doc.plugins.plugin import Plugin


@dataclass(frozen=True, slots=True)
class PluginLoadError:
    """Information about a plugin module that failed to load."""

    module_name: str
    message: str


@dataclass(frozen=True, slots=True)
class PluginLoadResult:
    """Loaded plugins plus isolated plugin failures."""

    plugins: tuple[Plugin, ...]
    errors: tuple[PluginLoadError, ...]


class PluginLoader:
    """Discover plugin instances from packages and optional directories."""

    def __init__(self, package_name: str, external_directory: Path | None = None, logger: logging.Logger | None = None) -> None:
        self._package_name = package_name
        self._external_directory = external_directory
        self._logger = logger

    def load(self) -> PluginLoadResult:
        """Load installed plugins while isolating broken plugin modules."""

        plugins: list[Plugin] = []
        errors: list[PluginLoadError] = []
        package = importlib.import_module(self._package_name)
        for module_info in sorted(pkgutil.iter_modules(package.__path__, f"{self._package_name}."), key=lambda item: item.name):
            try:
                module = importlib.import_module(module_info.name)
                factory = getattr(module, "create_plugin", None)
                if not callable(factory):
                    continue
                plugin = factory()
                if not isinstance(plugin, Plugin):
                    raise TypeError(f"{module_info.name}.create_plugin did not return Plugin")
                plugins.append(plugin)
            except Exception as error:  # noqa: BLE001 - plugin boundary isolation
                errors.append(PluginLoadError(module_info.name, str(error)))
                if self._logger is not None:
                    self._logger.exception("Failed to load plugin module %s", module_info.name)
        return PluginLoadResult(tuple(plugins), tuple(errors))
