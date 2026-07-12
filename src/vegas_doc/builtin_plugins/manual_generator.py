"""Manual Generator placeholder plugin."""

from __future__ import annotations

from vegas_doc.plugins.placeholders import PlaceholderPlugin
from vegas_doc.plugins.plugin import Plugin, PluginMetadata


def create_plugin() -> Plugin:
    """Return the Manual Generator plugin."""

    return PlaceholderPlugin(
        PluginMetadata(
            plugin_id="manual",
            name="Manual Generator",
            description="Workspace foundation for Manual Generator.",
            order=10,
        )
    )
