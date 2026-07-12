"""Application entry point."""

from __future__ import annotations

import logging
import sys

from PySide6.QtWidgets import QApplication

from vegas_doc.core.application_context import ApplicationContext, build_application_context
from vegas_doc.core.theme_manager import ThemeManager
from vegas_doc.plugins.loader import PluginLoader
from vegas_doc.plugins.manager import PluginManager
from vegas_doc.ui.main_window import MainWindow


def get_or_create_application(argv: list[str] | None = None) -> QApplication:
    """Return the existing QApplication or create one for production startup."""

    existing = QApplication.instance()
    if existing is not None:
        return existing
    return QApplication(argv or sys.argv)


def create_main_window(context: ApplicationContext | None = None) -> MainWindow:
    """Compose the application shell for production and tests."""

    app_context = context or build_application_context()
    logger = app_context.services.resolve(logging.Logger)
    loader = PluginLoader(app_context.settings.plugins_package, app_context.settings.external_plugins_directory, logger)
    manager = PluginManager(loader, logger=logger)
    return MainWindow(app_context, manager)


def main() -> int:
    """Run the Qt event loop."""

    app = get_or_create_application()
    context = build_application_context()
    context.services.resolve(ThemeManager).apply(app)
    window = create_main_window(context)
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
