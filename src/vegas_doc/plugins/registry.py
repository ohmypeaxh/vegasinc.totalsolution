"""Plugin registry."""

from __future__ import annotations

from vegas_doc.plugins.plugin import Plugin


class PluginRegistry:
    """Store installed plugins keyed by immutable plugin ID."""

    def __init__(self) -> None:
        self._plugins: dict[str, Plugin] = {}

    def register(self, plugin: Plugin) -> None:
        """Register a plugin instance, rejecting duplicate IDs."""

        plugin_id = plugin.metadata.plugin_id.strip()
        if not plugin_id:
            raise ValueError("Plugin ID cannot be empty")
        if plugin_id in self._plugins:
            raise ValueError(f"Duplicate plugin ID: {plugin_id}")
        self._plugins[plugin_id] = plugin

    def all(self) -> list[Plugin]:
        """Return plugins in deterministic navigation order."""

        return sorted(self._plugins.values(), key=lambda item: (item.metadata.order, item.metadata.name, item.metadata.plugin_id))
