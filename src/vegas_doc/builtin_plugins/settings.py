"""Settings plugin for OCR provider configuration."""

from __future__ import annotations

import sys

from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import QFormLayout, QGroupBox, QHBoxLayout, QLabel, QLineEdit, QPushButton, QSpinBox, QVBoxLayout, QWidget

from vegas_doc.core.application_context import ApplicationContext
from vegas_doc.core.config_manager import ConfigManager
from vegas_doc.plugins.plugin import Plugin, PluginMetadata
from vegas_doc.services.clova_ocr import ClovaOCRProvider, ClovaOCRSettings
from vegas_doc.services.secrets import KeyringSecretStore
from vegas_doc.version import BUILD_INFO


class ConnectionTestWorker(QThread):
    """Run CLOVA connection test away from the UI thread."""

    finished_with_status = Signal(bool, str)

    def __init__(self, provider: ClovaOCRProvider) -> None:
        super().__init__()
        self._provider = provider

    def run(self) -> None:
        try:
            from pathlib import Path

            from PySide6.QtCore import QBuffer, QByteArray, QIODevice
            from PySide6.QtGui import QColor, QImage, QPainter

            from vegas_doc.models.ocr import OCRPageRequest

            image = QImage(360, 120, QImage.Format_RGB32)
            image.fill(QColor("white"))
            painter = QPainter(image)
            painter.setPen(QColor("black"))
            painter.drawText(20, 65, "CLOVA OCR TEST 123")
            painter.end()
            data = QByteArray()
            buffer = QBuffer(data)
            buffer.open(QIODevice.WriteOnly)
            image.save(buffer, "PNG")
            provider_result = self._provider.recognize_page(OCRPageRequest(Path("clova_test.png"), 1, bytes(data), "image/png", "connection-test"))
            self.finished_with_status.emit(True, f"연결 성공: {provider_result.text[:60]}")
        except Exception as error:
            self.finished_with_status.emit(False, f"연결 실패: {error}")


class SettingsWidget(QWidget):
    """Real settings page for non-secret config and keyring secret storage."""

    def __init__(self, context: ApplicationContext) -> None:
        super().__init__()
        self._context = context
        self._config = context.services.resolve(ConfigManager)
        self._secret_store = KeyringSecretStore()
        values = self._config.load()
        self._worker: ConnectionTestWorker | None = None
        layout = QVBoxLayout(self)
        layout.setContentsMargins(42, 36, 42, 36)
        layout.setSpacing(8)
        eyebrow = QLabel("SYSTEM CONFIGURATION")
        eyebrow.setObjectName("Eyebrow")
        layout.addWidget(eyebrow)
        title = QLabel("Settings")
        title.setObjectName("PageTitle")
        layout.addWidget(title)
        subtitle = QLabel("제품 정보와 보안 OCR 연결 설정을 관리합니다.")
        subtitle.setObjectName("PageSubtitle")
        layout.addWidget(subtitle)
        layout.addSpacing(18)

        product_group = QGroupBox("Product Information")
        product_form = QFormLayout(product_group)
        for label, value in (
            ("Product", BUILD_INFO.product),
            ("Version", BUILD_INFO.version),
            ("Build", BUILD_INFO.build_number),
            ("Build Date", BUILD_INFO.build_date),
            ("Commit", BUILD_INFO.commit),
            ("Install Path", str(sys.executable)),
            ("Config Path", str(context.data_dir / context.settings.config_filename)),
            ("Log Path", str(context.data_dir / context.settings.log_directory_name)),
        ):
            field = QLineEdit(value)
            field.setReadOnly(True)
            product_form.addRow(label, field)
        layout.addWidget(product_group)

        ocr_group = QGroupBox("OCR Connection")
        form = QFormLayout(ocr_group)
        self.provider = QLineEdit("NAVER CLOVA OCR")
        self.provider.setReadOnly(True)
        self.url = QLineEdit(str(values.get("clova_invoke_url", "")))
        self.secret = QLineEdit(self._secret_store.get_secret("clova_secret_key"))
        self.secret.setEchoMode(QLineEdit.Password)
        self.timeout = QSpinBox()
        self.timeout.setRange(5, 300)
        self.timeout.setValue(int(values.get("clova_timeout_seconds", 60)))
        form.addRow("Provider", self.provider)
        form.addRow("Invoke URL", self.url)
        form.addRow("Secret Key", self.secret)
        form.addRow("Timeout (seconds)", self.timeout)
        layout.addWidget(ocr_group)
        buttons = QHBoxLayout()
        save = QPushButton("Save")
        save.setObjectName("PrimaryAction")
        test = QPushButton("Test Connection")
        save.clicked.connect(self.save)
        test.clicked.connect(self.test_connection)
        buttons.addWidget(save)
        buttons.addWidget(test)
        buttons.addStretch()
        layout.addLayout(buttons)
        self.status = QLabel("환경 변수 VEGAS_CLOVA_INVOKE_URL / VEGAS_CLOVA_SECRET_KEY도 지원합니다.")
        self.status.setWordWrap(True)
        layout.addWidget(self.status)
        layout.addStretch()

    def save(self) -> None:
        values = self._config.load()
        values["clova_invoke_url"] = self.url.text().strip()
        values["clova_timeout_seconds"] = self.timeout.value()
        self._config.save(values)
        self._secret_store.set_secret("clova_secret_key", self.secret.text().strip())
        self.status.setText("설정을 저장했습니다.")

    def test_connection(self) -> None:
        self.save()
        provider = ClovaOCRProvider(ClovaOCRSettings(self.url.text().strip(), self.timeout.value()), self._secret_store)
        status = provider.configuration_status()
        if not status.is_ready:
            self.status.setText("설정 확인 필요: " + ", ".join(status.messages))
            return
        self.status.setText("연결 테스트 중...")
        self._worker = ConnectionTestWorker(provider)
        self._worker.finished_with_status.connect(lambda ok, message: self.status.setText(message))
        self._worker.start()


class SettingsPlugin(Plugin):
    """Settings plugin implementation."""

    metadata = PluginMetadata("settings", "Settings", "Configure OCR provider settings.", 100)

    def create_widget(self, context: ApplicationContext) -> QWidget:
        return SettingsWidget(context)


def create_plugin() -> Plugin:
    """Return the Settings plugin."""

    return SettingsPlugin()
