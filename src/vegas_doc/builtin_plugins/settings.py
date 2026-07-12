"""Settings placeholder plugin."""

from __future__ import annotations

from vegas_doc.plugins.placeholders import PlaceholderPlugin
from vegas_doc.plugins.plugin import Plugin, PluginMetadata


def create_plugin() -> Plugin:
    """Return the Settings plugin."""

    return PlaceholderPlugin(
        PluginMetadata(
            plugin_id="settings",
            name="Settings",
            description="Workspace foundation for Settings.",
            order=100,
        )
    )
