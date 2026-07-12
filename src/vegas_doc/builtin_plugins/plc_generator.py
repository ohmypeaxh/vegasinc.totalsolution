"""PLC Generator placeholder plugin."""

from __future__ import annotations

from vegas_doc.plugins.placeholders import PlaceholderPlugin
from vegas_doc.plugins.plugin import Plugin, PluginMetadata


def create_plugin() -> Plugin:
    """Return the PLC Generator plugin."""

    return PlaceholderPlugin(
        PluginMetadata(
            plugin_id="plc",
            name="PLC Generator",
            description="Workspace foundation for PLC Generator.",
            order=70,
        )
    )
