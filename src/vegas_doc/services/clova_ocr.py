"""NAVER CLOVA OCR provider implementation."""

from __future__ import annotations

import base64
import os
import time
import uuid
from dataclasses import dataclass
from pathlib import Path

import requests

from vegas_doc.models.ocr import OCRConfigurationState, OCRConfigurationStatus, OCRPageRequest, OCRPageResult
from vegas_doc.services.ocr import OCRProvider
from vegas_doc.services.secrets import SecretStore


@dataclass(frozen=True, slots=True)
class ClovaOCRSettings:
    """Non-secret CLOVA OCR settings."""

    invoke_url: str = ""
    timeout_seconds: int = 60

    @classmethod
    def from_config(cls, values: dict[str, object]) -> "ClovaOCRSettings":
        """Create settings from config with environment URL fallback."""

        url = str(values.get("clova_invoke_url") or os.getenv("VEGAS_CLOVA_INVOKE_URL", ""))
        timeout = int(values.get("clova_timeout_seconds") or 60)
        return cls(url, timeout)


class ClovaOCRProvider(OCRProvider):
    """Provider-neutral adapter for NAVER CLOVA OCR."""

    def __init__(self, settings: ClovaOCRSettings, secret_store: SecretStore) -> None:
        self._settings = settings
        self._secret_store = secret_store

    @property
    def provider_name(self) -> str:
        return "NAVER CLOVA OCR"

    def configuration_status(self) -> OCRConfigurationStatus:
        """Validate non-secret URL and secret availability without exposing values."""

        messages: list[str] = []
        if not self._settings.invoke_url.strip():
            messages.append("CLOVA Invoke URL is missing")
        if not self._secret_store.get_secret("clova_secret_key"):
            messages.append("CLOVA secret key is missing")
        state = OCRConfigurationState.READY if not messages else OCRConfigurationState.MISSING_CONFIGURATION
        return OCRConfigurationStatus(state, self.provider_name, tuple(messages))

    def recognize_page(self, request: OCRPageRequest) -> OCRPageResult:
        """Send one page image to CLOVA and parse the response."""

        if not request.image_bytes:
            raise ValueError("CLOVA OCR requires image_bytes")
        secret = self._secret_store.get_secret("clova_secret_key")
        payload = self.build_payload(request)
        try:
            response = requests.post(
                self._settings.invoke_url,
                headers={"X-OCR-SECRET": secret, "Content-Type": "application/json"},
                json=payload,
                timeout=self._settings.timeout_seconds,
            )
        except requests.Timeout as error:
            raise TimeoutError("CLOVA OCR request timed out") from error
        except requests.ConnectionError as error:
            raise ConnectionError("CLOVA OCR connection failed") from error
        if not response.ok:
            raise RuntimeError(f"CLOVA OCR HTTP {response.status_code}")
        data = response.json()
        return self._parse_response(data, request.page_number)

    def build_payload(self, request: OCRPageRequest) -> dict[str, object]:
        """Build the CLOVA request body without secrets."""

        return {
            "version": "V2",
            "requestId": str(uuid.uuid4()),
            "timestamp": int(time.time() * 1000),
            "lang": "ko",
            "images": [
                {
                    "format": _format_for_path(request.source_path, request.mime_type),
                    "name": request.trace_id or f"page_{request.page_number}",
                    "data": base64.b64encode(request.image_bytes or b"").decode("ascii"),
                }
            ],
        }

    def _parse_response(self, data: dict[str, object], page_number: int) -> OCRPageResult:
        images = data.get("images", [])
        if not isinstance(images, list) or not images:
            raise RuntimeError("CLOVA OCR response did not include images")
        fields: list[str] = []
        confidences: list[float] = []
        for image in images:
            if not isinstance(image, dict):
                continue
            for field in image.get("fields", []) or []:
                if not isinstance(field, dict):
                    continue
                text = str(field.get("inferText", "")).strip()
                if text:
                    fields.append(text)
                confidence = field.get("inferConfidence")
                if isinstance(confidence, int | float):
                    confidences.append(float(confidence))
        confidence_value = sum(confidences) / len(confidences) if confidences else None
        return OCRPageResult(page_number, "\n".join(fields), confidence_value, provider_metadata={"provider": self.provider_name})


def _format_for_path(path: Path, mime_type: str | None) -> str:
    if mime_type and "/" in mime_type:
        return mime_type.rsplit("/", 1)[-1].replace("jpeg", "jpg")
    suffix = path.suffix.lower().lstrip(".")
    return "jpg" if suffix == "jpeg" else suffix or "png"
