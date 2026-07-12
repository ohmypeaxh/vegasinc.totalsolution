"""Application startup tests."""

from __future__ import annotations

import os

from conftest import require_qt

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


def test_main_window_starts_with_plugins(tmp_path) -> None:
    """The shell starts and renders all plugin placeholders."""

    require_qt()
    from vegas_doc.app.main import get_or_create_application
    from vegas_doc.config.defaults import AppSettings
    from vegas_doc.core.application_context import build_application_context
    from vegas_doc.plugins.loader import PluginLoader
    from vegas_doc.plugins.manager import PluginManager
    from vegas_doc.ui.main_window import MainWindow

    app = get_or_create_application([])
    context = build_application_context(AppSettings(), data_dir=tmp_path)
    window = MainWindow(context, PluginManager(PluginLoader(context.settings.plugins_package)))

    assert app is not None
    assert window.plugin_count == 10
    assert window.windowTitle() == "Vegas Total Solution Doc"
