"""Application About dialog."""

from __future__ import annotations

import platform
from pathlib import Path

from PySide6.QtCore import qVersion
from PySide6.QtWidgets import QDialog, QDialogButtonBox, QLabel, QVBoxLayout

from vegas_doc.version import BUILD_INFO


class AboutDialog(QDialog):
    """Display product identity and support-safe version information."""

    def __init__(
        self,
        version: str | None = None,
        parent=None,  # type: ignore[no-untyped-def]
        *,
        data_directory: Path | None = None,
        log_directory: Path | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("About Vegas Total Solution Doc")
        layout = QVBoxLayout(self)
        title = QLabel("Vegas Total Solution Doc")
        title.setObjectName("PageTitle")
        version_label = QLabel(f"Version {version or BUILD_INFO.version}")
        description = QLabel(
            "Internal document automation platform for Vegas Inc.\n"
            "Plugin-based architecture · PySide6 · Windows"
        )
        description.setWordWrap(True)
        privacy = QLabel("No credentials or customer documents are included in this preview.")
        privacy.setWordWrap(True)
        runtime = QLabel(
            f"Vegas Inc. · Copyright (c) Vegas Inc.\n"
            f"Python {platform.python_version()} · Qt {qVersion()}\n"
            f"Application data: {data_directory or 'per-user data directory'}\n"
            f"Logs: {log_directory or 'per-user logs directory'}"
        )
        runtime.setWordWrap(True)
        layout.addWidget(title)
        layout.addWidget(version_label)
        layout.addWidget(description)
        layout.addWidget(runtime)
        layout.addWidget(privacy)
        buttons = QDialogButtonBox(QDialogButtonBox.Close)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
