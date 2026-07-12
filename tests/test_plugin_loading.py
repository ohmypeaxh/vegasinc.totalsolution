"""Plugin loading tests."""

from __future__ import annotations

from conftest import require_qt


def test_builtin_plugins_load_in_navigation_order() -> None:
    """Built-in placeholder modules are discovered without MainWindow changes."""

    require_qt()
    from vegas_doc.config.defaults import AppSettings
    from vegas_doc.core.application_context import build_application_context
    from vegas_doc.plugins.loader import PluginLoader
    from vegas_doc.plugins.manager import PluginManager

    context = build_application_context(AppSettings())
    plugins = PluginManager(PluginLoader(context.settings.plugins_package)).load_installed()

    assert [plugin.metadata.name for plugin in plugins] == [
        "Manual Generator",
        "DQ Generator",
        "IQ Generator",
        "OQ Generator",
        "PQ Generator",
        "URS OCR",
        "PLC Generator",
        "Alarm Generator",
        "Excel Helper",
        "Settings",
    ]
