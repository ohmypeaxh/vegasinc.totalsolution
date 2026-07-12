"""URS OCR placeholder plugin."""

from __future__ import annotations

from vegas_doc.plugins.placeholders import PlaceholderPlugin
from vegas_doc.plugins.plugin import Plugin, PluginMetadata


def create_plugin() -> Plugin:
    """Return the URS OCR plugin."""

    return PlaceholderPlugin(
        PluginMetadata(
            plugin_id="urs_ocr",
            name="URS OCR",
            description="Workspace foundation for URS OCR.",
            order=60,
        )
    )
