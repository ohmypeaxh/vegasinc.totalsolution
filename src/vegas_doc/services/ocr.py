"""Provider-neutral OCR service abstractions and orchestration."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable

from vegas_doc.models.ocr import OCRConfigurationStatus, OCRPageError, OCRPageRequest, OCRPageResult, OCRRequest, OCRResult

CancellationToken = Callable[[], bool]


class OCRProvider(ABC):
    """Provider boundary for OCR engines such as future CLOVA integrations."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return a provider display name."""

    @abstractmethod
    def configuration_status(self) -> OCRConfigurationStatus:
        """Return readiness without exposing credentials or endpoints."""

    @abstractmethod
    def recognize_page(self, request: OCRPageRequest) -> OCRPageResult:
        """Recognize text for one page or raise a provider-specific exception."""


class OCRService(ABC):
    """OCR orchestration contract with page isolation and cancellation readiness."""

    @abstractmethod
    def recognize(self, request: OCRRequest, cancellation_token: CancellationToken | None = None) -> OCRResult:
        """Recognize a request and isolate failures by page."""


class ProviderOCRService(OCRService):
    """Default OCR orchestration that delegates each page to a provider."""

    def __init__(self, provider: OCRProvider) -> None:
        self._provider = provider

    def recognize(self, request: OCRRequest, cancellation_token: CancellationToken | None = None) -> OCRResult:
        """Recognize pages until cancelled, preserving page-level failures."""

        status = self._provider.configuration_status()
        if not status.is_ready:
            errors = tuple(
                OCRPageError(page.page_number, status.state.value, "; ".join(status.messages) or "OCR provider is not configured")
                for page in request.pages
            )
            return OCRResult(errors=errors)

        pages: list[OCRPageResult] = []
        errors: list[OCRPageError] = []
        for page_request in request.pages:
            if cancellation_token is not None and cancellation_token():
                return OCRResult(tuple(pages), tuple(errors), cancelled=True)
            try:
                pages.append(self._provider.recognize_page(page_request))
            except Exception as error:  # noqa: BLE001 - provider boundary isolation
                errors.append(OCRPageError(page_request.page_number, type(error).__name__, str(error), retryable=False))
        return OCRResult(tuple(pages), tuple(errors))
