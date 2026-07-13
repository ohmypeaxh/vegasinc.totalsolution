"""Main window with plugin-driven navigation."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from vegas_doc.core.application_context import ApplicationContext
from vegas_doc.core.resource_manager import ResourceManager
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
        self._navigation.setObjectName("SidebarNavigation")
        self._workspace = QStackedWidget()
        self._workspace.setObjectName("Workspace")
        self.setWindowTitle(context.settings.app_name)
        icon_path = context.services.resolve(ResourceManager).branding_path("app.ico")
        if icon_path is not None:
            self.setWindowIcon(QIcon(str(icon_path)))
        self.setMinimumSize(1180, 760)
        self.resize(1440, 900)
        self._build_shell()
        self.load_plugins()

    def _build_shell(self) -> None:
        """Build static shell widgets for navigation and plugin workspace."""

        container = QWidget()
        container.setObjectName("AppShell")
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(280)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(22, 24, 22, 22)
        sidebar_layout.setSpacing(10)

        sidebar_layout.addWidget(self._build_brand_header())
        sidebar_layout.addSpacing(20)
        navigation_caption = QLabel("WORKSPACE")
        navigation_caption.setObjectName("NavigationCaption")
        sidebar_layout.addWidget(navigation_caption)

        self._navigation.setSpacing(4)
        self._navigation.setUniformItemSizes(True)
        self._navigation.setFocusPolicy(Qt.NoFocus)
        self._navigation.currentRowChanged.connect(self._workspace.setCurrentIndex)
        sidebar_layout.addWidget(self._navigation, 1)

        footer = QLabel("VEGAS INC.\nINTERNAL DOCUMENT PLATFORM")
        footer.setObjectName("SidebarFooter")
        sidebar_layout.addWidget(footer)

        content = QFrame()
        content.setObjectName("ContentArea")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(20, 18, 20, 18)
        content_layout.addWidget(self._workspace)

        layout.addWidget(sidebar)
        layout.addWidget(content, 1)
        self.setCentralWidget(container)

    def _build_brand_header(self) -> QFrame:
        """Build the Vegas identity card shown at the top of the sidebar."""

        card = QFrame()
        card.setObjectName("BrandCard")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(15, 13, 15, 12)
        card_layout.setSpacing(2)

        logo = QLabel()
        logo.setObjectName("BrandLogo")
        logo.setAlignment(Qt.AlignCenter)
        logo_path = self._context.services.resolve(ResourceManager).branding_path("vegas_logo.png")
        if logo_path is not None:
            pixmap = QPixmap(str(logo_path))
            logo.setPixmap(pixmap.scaled(210, 74, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            logo.setText("Vegas")
        card_layout.addWidget(logo)

        product = QLabel("TOTAL SOLUTION DOC")
        product.setObjectName("BrandProduct")
        product.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(product)
        return card

    def load_plugins(self) -> None:
        """Load installed plugins into left navigation and right workspace."""

        self._plugins = self._plugin_manager.load_installed()
        for plugin in self._plugins:
            item = QListWidgetItem(plugin.metadata.name)
            item.setData(Qt.UserRole, plugin.metadata.plugin_id)
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
