"""First-run onboarding dialog used by the application and UI previews."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QSpinBox,
    QVBoxLayout,
)


class OnboardingWizard(QDialog):
    """Collect the minimum non-secret settings needed for first use."""

    def __init__(self, parent=None) -> None:  # type: ignore[no-untyped-def]
        super().__init__(parent)
        self.setWindowTitle("Vegas Total Solution Doc - First Run")
        self.setModal(True)
        layout = QVBoxLayout(self)
        title = QLabel("Welcome to Vegas Total Solution Doc")
        title.setObjectName("PageTitle")
        description = QLabel(
            "Configure the document template and optional CLOVA OCR connection. "
            "You can change these values later in Settings."
        )
        description.setWordWrap(True)
        layout.addWidget(title)
        layout.addWidget(description)

        form = QFormLayout()
        self.template_path = QLineEdit()
        self.invoke_url = QLineEdit()
        self.invoke_url.setPlaceholderText("https://example.invalid/clova-ocr")
        self.secret_key = QLineEdit()
        self.secret_key.setEchoMode(QLineEdit.Password)
        self.secret_key.setPlaceholderText("Stored securely; never written to project files")
        self.timeout = QSpinBox()
        self.timeout.setRange(5, 300)
        self.timeout.setValue(60)
        self.configure_later = QCheckBox("Configure OCR later")
        form.addRow("Default DOCX template", self.template_path)
        form.addRow("CLOVA Invoke URL", self.invoke_url)
        form.addRow("CLOVA Secret Key", self.secret_key)
        form.addRow("Timeout (seconds)", self.timeout)
        form.addRow("", self.configure_later)
        layout.addLayout(form)

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
