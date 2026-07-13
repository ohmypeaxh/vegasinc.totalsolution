"""Application entry point."""

from __future__ import annotations

import logging
import sys

from PySide6.QtWidgets import QApplication, QMessageBox

from vegas_doc.core.application_context import ApplicationContext, build_application_context
from vegas_doc.core.resource_manager import ResourceManager
from vegas_doc.core.single_instance import SingleInstanceGuard
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
    app.setApplicationName(context.settings.app_name)
    app.setOrganizationName(context.settings.organization_name)
    icon_path = context.services.resolve(ResourceManager).branding_path("app.ico")
    if icon_path is not None:
        from PySide6.QtGui import QIcon

        app.setWindowIcon(QIcon(str(icon_path)))
    instance_guard = SingleInstanceGuard(context.data_dir)
    if not instance_guard.acquire():
        QMessageBox.information(None, "Vegas Total Solution Doc", "프로그램이 이미 실행 중입니다.")
        return 0
    context.services.resolve(ThemeManager).apply(app)
    window = create_main_window(context)
    window.show()
    try:
        return app.exec()
    finally:
        instance_guard.release()


if __name__ == "__main__":
    raise SystemExit(main())
