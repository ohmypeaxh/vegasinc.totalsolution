"""Application About dialog."""

from __future__ import annotations

from PySide6.QtWidgets import QDialog, QDialogButtonBox, QLabel, QVBoxLayout


class AboutDialog(QDialog):
    """Display product identity and support-safe version information."""

    def __init__(self, version: str = "0.1.0", parent=None) -> None:  # type: ignore[no-untyped-def]
        super().__init__(parent)
        self.setWindowTitle("About Vegas Total Solution Doc")
        layout = QVBoxLayout(self)
        title = QLabel("Vegas Total Solution Doc")
        title.setObjectName("PageTitle")
        version_label = QLabel(f"Version {version}")
        description = QLabel(
            "Internal document automation platform for Vegas Inc.\n"
            "Plugin-based architecture · PySide6 · Windows"
        )
        description.setWordWrap(True)
        privacy = QLabel("No credentials or customer documents are included in this preview.")
        privacy.setWordWrap(True)
        layout.addWidget(title)
        layout.addWidget(version_label)
        layout.addWidget(description)
        layout.addWidget(privacy)
        buttons = QDialogButtonBox(QDialogButtonBox.Close)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
