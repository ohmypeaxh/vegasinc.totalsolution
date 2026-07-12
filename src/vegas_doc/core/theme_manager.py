"""Qt theme application service."""

from __future__ import annotations

from PySide6.QtWidgets import QApplication


class ThemeManager:
    """Apply application-wide visual styling."""

    def apply(self, app: QApplication) -> None:
        """Apply a conservative light theme suitable for enterprise desktops."""

        app.setStyleSheet("QListWidget::item { padding: 10px; } QLabel#PageTitle { font-size: 22px; font-weight: 700; }")
