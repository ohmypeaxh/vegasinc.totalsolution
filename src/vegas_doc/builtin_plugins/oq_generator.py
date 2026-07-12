"""OQ Generator placeholder plugin."""

from __future__ import annotations

from vegas_doc.plugins.placeholders import PlaceholderPlugin
from vegas_doc.plugins.plugin import Plugin, PluginMetadata


def create_plugin() -> Plugin:
    """Return the OQ Generator plugin."""

    return PlaceholderPlugin(
        PluginMetadata(
            plugin_id="oq",
            name="OQ Generator",
            description="Workspace foundation for OQ Generator.",
            order=40,
        )
    )
