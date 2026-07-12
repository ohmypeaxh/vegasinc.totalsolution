"""Document text extraction contracts and traceable result models."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path


class DocumentKind(StrEnum):
    """Supported source document kinds for future extractors."""

    SEARCHABLE_PDF = "searchable_pdf"
    SCANNED_PDF = "scanned_pdf"
    MIXED_PDF = "mixed_pdf"
    IMAGE = "image"


class ExtractionMethod(StrEnum):
    """Method used to obtain page text."""

    EMBEDDED_TEXT = "embedded_text"
    OCR = "ocr"
    MANUAL = "manual"
    NOT_EXTRACTED = "not_extracted"


@dataclass(frozen=True, slots=True)
class ExtractionPolicy:
    """Policy contract for choosing embedded text before OCR when possible."""

    prefer_embedded_text: bool = True
    allow_ocr_fallback: bool = True

    def choose_method(self, has_embedded_text: bool, is_scanned: bool) -> ExtractionMethod:
        """Select an extraction method for a page without performing extraction."""

        if self.prefer_embedded_text and has_embedded_text:
            return ExtractionMethod.EMBEDDED_TEXT
        if self.allow_ocr_fallback and is_scanned:
            return ExtractionMethod.OCR
        return ExtractionMethod.NOT_EXTRACTED


@dataclass(frozen=True, slots=True)
class PageExtractionMetadata:
    """Traceable extraction metadata for one source page."""

    source_path: Path
    page_number: int
    document_kind: DocumentKind
    extraction_method: ExtractionMethod
    original_text: str
    normalized_text: str | None = None
    reviewed_text: str | None = None
    confidence: float | None = None
    warnings: tuple[str, ...] = ()
    errors: tuple[str, ...] = ()
    trace_id: str | None = None

    def __post_init__(self) -> None:
        if self.page_number < 1:
            raise ValueError("page_number must be one-based")
        if self.confidence is not None and not 0 <= self.confidence <= 1:
            raise ValueError("confidence must be between 0 and 1")


@dataclass(frozen=True, slots=True)
class DocumentExtractionResult:
    """Extraction result for a document with page-level traceability."""

    source_path: Path
    document_kind: DocumentKind
    pages: tuple[PageExtractionMetadata, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        for page in self.pages:
            if page.source_path != self.source_path:
                raise ValueError("page source_path must match document source_path")
