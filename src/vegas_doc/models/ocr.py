"""Provider-neutral OCR request and result models."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any


class OCRConfigurationState(StrEnum):
    """Readiness state for an OCR provider configuration boundary."""

    READY = "ready"
    MISSING_CONFIGURATION = "missing_configuration"
    INVALID_CONFIGURATION = "invalid_configuration"


@dataclass(frozen=True, slots=True)
class OCRConfigurationStatus:
    """Typed provider configuration readiness without exposing secrets."""

    state: OCRConfigurationState
    provider_name: str
    messages: tuple[str, ...] = ()

    @property
    def is_ready(self) -> bool:
        """Return whether OCR requests may be submitted."""

        return self.state is OCRConfigurationState.READY


@dataclass(frozen=True, slots=True)
class OCRPageRequest:
    """OCR request for a single source page or image."""

    source_path: Path
    page_number: int
    image_bytes: bytes | None = None
    mime_type: str | None = None
    trace_id: str | None = None

    def __post_init__(self) -> None:
        if self.page_number < 1:
            raise ValueError("page_number must be one-based")


@dataclass(frozen=True, slots=True)
class OCRRequest:
    """Provider-neutral OCR request composed of page-level requests."""

    pages: tuple[OCRPageRequest, ...]
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.pages:
            raise ValueError("OCRRequest requires at least one page")


@dataclass(frozen=True, slots=True)
class OCRPageError:
    """OCR failure isolated to a single page."""

    page_number: int
    code: str
    message: str
    retryable: bool = False

    def __post_init__(self) -> None:
        if self.page_number < 1:
            raise ValueError("page_number must be one-based")


@dataclass(frozen=True, slots=True)
class OCRPageResult:
    """OCR result for one page, preserving provider metadata safely."""

    page_number: int
    text: str
    confidence: float | None = None
    warnings: tuple[str, ...] = ()
    provider_metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.page_number < 1:
            raise ValueError("page_number must be one-based")
        if self.confidence is not None and not 0 <= self.confidence <= 1:
            raise ValueError("confidence must be between 0 and 1")


@dataclass(frozen=True, slots=True)
class OCRResult:
    """Aggregated OCR result with page-level successes and failures."""

    pages: tuple[OCRPageResult, ...] = ()
    errors: tuple[OCRPageError, ...] = ()
    cancelled: bool = False

    @property
    def has_errors(self) -> bool:
        """Return whether any page failed."""

        return bool(self.errors)
