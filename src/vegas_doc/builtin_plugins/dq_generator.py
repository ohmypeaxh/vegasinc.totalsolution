"""DQ Generator placeholder plugin."""

from __future__ import annotations

from vegas_doc.plugins.placeholders import PlaceholderPlugin
from vegas_doc.plugins.plugin import Plugin, PluginMetadata


def create_plugin() -> Plugin:
    """Return the DQ Generator plugin."""

    return PlaceholderPlugin(
        PluginMetadata(
            plugin_id="dq",
            name="DQ Generator",
            description="Workspace foundation for DQ Generator.",
            order=20,
        )
    )
