"""DQ mapping and response models for future traceability."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from vegas_doc.models.common import ReviewStatus


class MappingRelationship(StrEnum):
    """Supported relationships between URS requirements and DQ outputs."""

    ONE_TO_ONE = "one_to_one"
    ONE_TO_MANY = "one_to_many"
    MANY_TO_ONE = "many_to_one"
    EXCLUDED = "excluded"
    NOT_APPLICABLE = "not_applicable"
    USER_RESPONSE = "user_response"
    UNMAPPED = "unmapped"


@dataclass(frozen=True, slots=True)
class DQResponse:
    """User-authored DQ response placeholder with traceability."""

    response_id: str
    text: str
    author: str | None = None

    def __post_init__(self) -> None:
        if not self.response_id.strip():
            raise ValueError("response_id is required")


@dataclass(frozen=True, slots=True)
class DQMapping:
    """Traceable mapping between URS requirements and future DQ sections/responses."""

    mapping_id: str
    relationship: MappingRelationship
    source_requirement_ids: tuple[str, ...] = field(default_factory=tuple)
    dq_section_ids: tuple[str, ...] = field(default_factory=tuple)
    source_pages: tuple[int, ...] = field(default_factory=tuple)
    dq_response: DQResponse | None = None
    review_status: ReviewStatus = ReviewStatus.NOT_REVIEWED
    rationale: str | None = None

    def __post_init__(self) -> None:
        if not self.mapping_id.strip():
            raise ValueError("mapping_id is required")
        if any(page < 1 for page in self.source_pages):
            raise ValueError("source_pages must be one-based")
        if self.relationship in {MappingRelationship.EXCLUDED, MappingRelationship.NOT_APPLICABLE} and not self.rationale:
            raise ValueError("excluded/not-applicable mappings require rationale")
