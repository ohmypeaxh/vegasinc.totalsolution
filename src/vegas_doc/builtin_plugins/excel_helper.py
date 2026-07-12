"""Excel Helper placeholder plugin."""

from __future__ import annotations

from vegas_doc.plugins.placeholders import PlaceholderPlugin
from vegas_doc.plugins.plugin import Plugin, PluginMetadata


def create_plugin() -> Plugin:
    """Return the Excel Helper plugin."""

    return PlaceholderPlugin(
        PluginMetadata(
            plugin_id="excel",
            name="Excel Helper",
            description="Workspace foundation for Excel Helper.",
            order=90,
        )
    )
