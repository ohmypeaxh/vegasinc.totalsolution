"""Alarm Generator placeholder plugin."""

from __future__ import annotations

from vegas_doc.plugins.placeholders import PlaceholderPlugin
from vegas_doc.plugins.plugin import Plugin, PluginMetadata


def create_plugin() -> Plugin:
    """Return the Alarm Generator plugin."""

    return PlaceholderPlugin(
        PluginMetadata(
            plugin_id="alarm",
            name="Alarm Generator",
            description="Workspace foundation for Alarm Generator.",
            order=80,
        )
    )
