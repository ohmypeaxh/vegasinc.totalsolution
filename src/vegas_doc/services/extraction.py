"""Document extraction abstractions without concrete PDF/OCR implementation."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from vegas_doc.models.extraction import DocumentExtractionResult, DocumentKind, ExtractionMethod, ExtractionPolicy


class DocumentTextExtractor(ABC):
    """Interface for searchable PDFs, scanned PDFs, mixed PDFs, and images."""

    @abstractmethod
    def supports(self, source_path: Path, document_kind: DocumentKind) -> bool:
        """Return whether this extractor can handle the source kind."""

    @abstractmethod
    def extract(self, source_path: Path, document_kind: DocumentKind, policy: ExtractionPolicy) -> DocumentExtractionResult:
        """Extract text according to policy without performing unrelated business logic."""


class ExtractionPolicyEvaluator:
    """Small policy helper used by tests and future extractors."""

    def __init__(self, policy: ExtractionPolicy) -> None:
        self._policy = policy

    def method_for_page(self, has_embedded_text: bool, is_scanned: bool) -> ExtractionMethod:
        """Return the method a conforming extractor should use for a page."""

        return self._policy.choose_method(has_embedded_text, is_scanned)
