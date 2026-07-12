"""Plugin discovery and loading."""

from __future__ import annotations

import importlib
import pkgutil
from pathlib import Path

from vegas_doc.plugins.plugin import Plugin


class PluginLoader:
    """Discover plugin instances from packages and optional directories."""

    def __init__(self, package_name: str, external_directory: Path | None = None) -> None:
        self._package_name = package_name
        self._external_directory = external_directory

    def load(self) -> list[Plugin]:
        """Load all installed plugins."""

        plugins: list[Plugin] = []
        package = importlib.import_module(self._package_name)
        for module_info in pkgutil.iter_modules(package.__path__, f"{self._package_name}."):
            module = importlib.import_module(module_info.name)
            factory = getattr(module, "create_plugin", None)
            if callable(factory):
                plugin = factory()
                if not isinstance(plugin, Plugin):
                    raise TypeError(f"{module_info.name}.create_plugin did not return Plugin")
                plugins.append(plugin)
        return plugins
