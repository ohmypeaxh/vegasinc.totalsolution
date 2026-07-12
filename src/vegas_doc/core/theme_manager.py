"""Qt theme application service."""

from __future__ import annotations

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

        if self._theme_path is not None and self._theme_path.exists():
            app.setStyleSheet(self._theme_path.read_text(encoding="utf-8"))
            return
        app.setStyleSheet("QListWidget::item { padding: 10px; } QLabel#PageTitle { font-size: 22px; font-weight: 700; }")
