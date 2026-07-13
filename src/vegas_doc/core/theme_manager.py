"""Qt theme application service."""

from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from PySide6.QtWidgets import QApplication


class ThemeManager:
    """Apply application-wide visual styling with safe missing-theme behavior."""

    def __init__(self, theme_path: Path | None = None) -> None:
        self._theme_path = theme_path

    def apply(self, app: "QApplication") -> None:
        """Apply a stylesheet from disk when present, otherwise use a default style."""

        self._install_preferred_font(app)
        if self._theme_path is not None and self._theme_path.exists():
            app.setStyleSheet(self._theme_path.read_text(encoding="utf-8"))
            return
        app.setStyleSheet(
            "QListWidget::item { padding: 12px; } "
            "QLabel#PageTitle { color: #1e1a2c; font-size: 26px; font-weight: 700; } "
            "QPushButton#PrimaryAction { color: white; background: #8d58ff; padding: 9px 16px; }"
        )

    @staticmethod
    def _install_preferred_font(app: "QApplication") -> None:
        """Register the Windows Korean UI font, including for offscreen rendering."""

        from PySide6.QtGui import QFont, QFontDatabase

        family = "Malgun Gothic"
        if family not in QFontDatabase.families():
            windows_directory = Path(os.environ.get("WINDIR", r"C:\Windows"))
            font_path = windows_directory / "Fonts" / "malgun.ttf"
            if font_path.is_file():
                font_id = QFontDatabase.addApplicationFont(str(font_path))
                families = QFontDatabase.applicationFontFamilies(font_id)
                if families:
                    family = families[0]
        app.setFont(QFont(family, 10))
