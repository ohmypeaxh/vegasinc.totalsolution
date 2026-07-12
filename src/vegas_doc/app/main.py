"""Application entry point."""

from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from vegas_doc.core.application_context import build_application_context
from vegas_doc.core.theme_manager import ThemeManager
from vegas_doc.plugins.loader import PluginLoader
from vegas_doc.plugins.manager import PluginManager
from vegas_doc.ui.main_window import MainWindow


def create_main_window() -> MainWindow:
    """Compose the application shell for production and tests."""

    context = build_application_context()
    loader = PluginLoader(context.settings.plugins_package, context.settings.external_plugins_directory)
    manager = PluginManager(loader)
    return MainWindow(context, manager)


def main() -> int:
    """Run the Qt event loop."""

    app = QApplication(sys.argv)
    window = create_main_window()
    theme = window._context.services.resolve("theme", ThemeManager)
    theme.apply(app)
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
