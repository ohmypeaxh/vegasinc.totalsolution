"""Shared domain value objects and enums for document automation."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path


class ReviewStatus(StrEnum):
    """Human review state for traceable project data."""

    NOT_REVIEWED = "not_reviewed"
    NEEDS_REVIEW = "needs_review"
    REVIEWED = "reviewed"
    APPROVED = "approved"


@dataclass(frozen=True, slots=True)
class SourceReference:
    """Traceable reference to a source document and optional page/section."""

    document_path: Path
    page_number: int | None = None
    section: str | None = None

    def __post_init__(self) -> None:
        if self.page_number is not None and self.page_number < 1:
            raise ValueError("page_number must be one-based when provided")
