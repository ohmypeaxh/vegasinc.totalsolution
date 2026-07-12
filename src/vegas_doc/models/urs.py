"""URS requirement domain models."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path


class RequirementPriority(StrEnum):
    """Requirement priority values for future customer strategies."""

    UNSPECIFIED = "unspecified"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class VerificationMethod(StrEnum):
    """Verification method classification values."""

    UNSPECIFIED = "unspecified"
    INSPECTION = "inspection"
    TEST = "test"
    ANALYSIS = "analysis"
    DEMONSTRATION = "demonstration"


@dataclass(frozen=True, slots=True)
class URSRequirement:
    """Traceable URS requirement preserving original and edited text distinctly."""

    requirement_id: str
    source_document: Path
    source_page: int
    source_section: str | None
    original_text: str
    normalized_text: str
    category: str | None = None
    subcategory: str | None = None
    priority: RequirementPriority = RequirementPriority.UNSPECIFIED
    verification_method: VerificationMethod = VerificationMethod.UNSPECIFIED
    dq_section: str | None = None
    confidence: float | None = None
    included: bool = True
    user_reviewed: bool = False
    user_notes: str | None = None

    def __post_init__(self) -> None:
        if not self.requirement_id.strip():
            raise ValueError("requirement_id is required")
        if self.source_page < 1:
            raise ValueError("source_page must be one-based")
        if not self.original_text.strip():
            raise ValueError("original_text is required")
        if not self.normalized_text.strip():
            raise ValueError("normalized_text is required")
        if self.confidence is not None and not 0 <= self.confidence <= 1:
            raise ValueError("confidence must be between 0 and 1")
