"""IQ Generator placeholder plugin."""

from __future__ import annotations

from vegas_doc.plugins.placeholders import PlaceholderPlugin
from vegas_doc.plugins.plugin import Plugin, PluginMetadata


def create_plugin() -> Plugin:
    """Return the IQ Generator plugin."""

    return PlaceholderPlugin(
        PluginMetadata(
            plugin_id="iq",
            name="IQ Generator",
            description="Workspace foundation for IQ Generator.",
            order=30,
        )
    )
