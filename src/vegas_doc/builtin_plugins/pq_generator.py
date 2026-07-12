"""PQ Generator placeholder plugin."""

from __future__ import annotations

from vegas_doc.plugins.placeholders import PlaceholderPlugin
from vegas_doc.plugins.plugin import Plugin, PluginMetadata


def create_plugin() -> Plugin:
    """Return the PQ Generator plugin."""

    return PlaceholderPlugin(
        PluginMetadata(
            plugin_id="pq",
            name="PQ Generator",
            description="Workspace foundation for PQ Generator.",
            order=50,
        )
    )
