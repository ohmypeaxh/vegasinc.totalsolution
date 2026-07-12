"""Phase 2 OCR and extraction contract tests."""

from __future__ import annotations

from pathlib import Path

from vegas_doc.models.extraction import DocumentKind, ExtractionMethod, ExtractionPolicy
from vegas_doc.models.ocr import OCRConfigurationState, OCRConfigurationStatus, OCRPageRequest, OCRPageResult, OCRRequest
from vegas_doc.services.extraction import ExtractionPolicyEvaluator
from vegas_doc.services.ocr import OCRProvider, ProviderOCRService


class FakeOCRProvider(OCRProvider):
    """Fake provider that can fail selected pages without real network calls."""

    def __init__(self, ready: bool = True, fail_pages: set[int] | None = None) -> None:
        self._ready = ready
        self._fail_pages = fail_pages or set()

    @property
    def provider_name(self) -> str:
        return "fake"

    def configuration_status(self) -> OCRConfigurationStatus:
        if self._ready:
            return OCRConfigurationStatus(OCRConfigurationState.READY, self.provider_name)
        return OCRConfigurationStatus(OCRConfigurationState.MISSING_CONFIGURATION, self.provider_name, ("missing secure config",))

    def recognize_page(self, request: OCRPageRequest) -> OCRPageResult:
        if request.page_number in self._fail_pages:
            raise RuntimeError(f"page {request.page_number} failed")
        return OCRPageResult(request.page_number, f"text {request.page_number}", confidence=0.9)


def test_ocr_provider_configuration_not_ready_status() -> None:
    """Provider configuration status exposes readiness without secrets."""

    status = FakeOCRProvider(ready=False).configuration_status()

    assert status.state is OCRConfigurationState.MISSING_CONFIGURATION
    assert not status.is_ready
    assert "missing secure config" in status.messages


def test_ocr_service_isolates_page_failures() -> None:
    """OCR orchestration preserves successful pages when one page fails."""

    request = OCRRequest(
        (
            OCRPageRequest(Path("urs.pdf"), 1),
            OCRPageRequest(Path("urs.pdf"), 2),
            OCRPageRequest(Path("urs.pdf"), 3),
        )
    )
    result = ProviderOCRService(FakeOCRProvider(fail_pages={2})).recognize(request)

    assert [page.page_number for page in result.pages] == [1, 3]
    assert [error.page_number for error in result.errors] == [2]
    assert result.has_errors


def test_extraction_policy_prefers_embedded_text_before_ocr() -> None:
    """Searchable and mixed page policy prefers embedded text before OCR."""

    evaluator = ExtractionPolicyEvaluator(ExtractionPolicy(prefer_embedded_text=True, allow_ocr_fallback=True))

    assert evaluator.method_for_page(has_embedded_text=True, is_scanned=False) is ExtractionMethod.EMBEDDED_TEXT
    assert evaluator.method_for_page(has_embedded_text=False, is_scanned=True) is ExtractionMethod.OCR
    assert evaluator.method_for_page(has_embedded_text=False, is_scanned=False) is ExtractionMethod.NOT_EXTRACTED
    assert DocumentKind.SEARCHABLE_PDF.value == "searchable_pdf"
    assert DocumentKind.SCANNED_PDF.value == "scanned_pdf"
    assert DocumentKind.MIXED_PDF.value == "mixed_pdf"
    assert DocumentKind.IMAGE.value == "image"
