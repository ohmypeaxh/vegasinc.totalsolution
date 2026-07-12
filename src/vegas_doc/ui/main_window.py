"""Main window with plugin-driven navigation."""

from __future__ import annotations

from PySide6.QtWidgets import QHBoxLayout, QListWidget, QListWidgetItem, QMainWindow, QStackedWidget, QWidget

from vegas_doc.core.application_context import ApplicationContext
from vegas_doc.plugins.manager import PluginManager
from vegas_doc.plugins.plugin import Plugin


class MainWindow(QMainWindow):
    """Shell window that renders installed plugins without module-specific code."""

    def __init__(self, context: ApplicationContext, plugin_manager: PluginManager) -> None:
        super().__init__()
        self._context = context
        self._plugin_manager = plugin_manager
        self._plugins: list[Plugin] = []
        self._navigation = QListWidget()
        self._workspace = QStackedWidget()
        self.setWindowTitle(context.settings.app_name)
        self.resize(1100, 760)
        self._build_shell()
        self.load_plugins()

    def _build_shell(self) -> None:
        """Build static shell widgets for navigation and plugin workspace."""

        container = QWidget()
        layout = QHBoxLayout(container)
        self._navigation.setFixedWidth(240)
        self._navigation.currentRowChanged.connect(self._workspace.setCurrentIndex)
        layout.addWidget(self._navigation)
        layout.addWidget(self._workspace, 1)
        self.setCentralWidget(container)

    def load_plugins(self) -> None:
        """Load installed plugins into left navigation and right workspace."""

        self._plugins = self._plugin_manager.load_installed()
        for plugin in self._plugins:
            item = QListWidgetItem(plugin.metadata.name)
            item.setData(256, plugin.metadata.plugin_id)
            self._navigation.addItem(item)
            page = plugin.create_widget(self._context)
            if not isinstance(page, QWidget):
                raise TypeError(f"Plugin {plugin.metadata.plugin_id} did not return a QWidget")
            self._workspace.addWidget(page)
        if self._plugins:
            self._navigation.setCurrentRow(0)

    @property
    def plugin_count(self) -> int:
        """Return the number of loaded plugin pages."""

        return len(self._plugins)
