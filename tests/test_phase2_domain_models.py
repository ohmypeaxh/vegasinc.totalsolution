"""Phase 2 URS and DQ mapping model tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from vegas_doc.models.dq_mapping import DQMapping, DQResponse, MappingRelationship
from vegas_doc.models.urs import RequirementPriority, URSRequirement, VerificationMethod


def test_urs_requirement_preserves_traceability_and_edited_text() -> None:
    """Original text remains distinct from normalized/reviewed domain fields."""

    requirement = URSRequirement(
        requirement_id="URS-001",
        source_document=Path("URS.pdf"),
        source_page=3,
        source_section="6.1",
        original_text=" Pump shall stop on alarm. ",
        normalized_text="Pump shall stop on alarm.",
        category="safety",
        subcategory="alarm",
        priority=RequirementPriority.HIGH,
        verification_method=VerificationMethod.TEST,
        dq_section="Safety Controls",
        confidence=0.87,
        user_reviewed=True,
        user_notes="Reviewed by QA",
    )

    assert requirement.original_text == " Pump shall stop on alarm. "
    assert requirement.normalized_text == "Pump shall stop on alarm."
    assert requirement.source_page == 3
    assert requirement.included


def test_urs_requirement_validation_rejects_missing_original_text() -> None:
    """Requirements must preserve non-empty original source text."""

    with pytest.raises(ValueError, match="original_text"):
        URSRequirement("URS-002", Path("URS.pdf"), 1, None, "", "normalized")


def test_requirement_exclusion_and_mapping_relationship_serialization_shape() -> None:
    """Exclusion and user-response mapping models preserve traceability."""

    excluded = DQMapping(
        mapping_id="MAP-001",
        relationship=MappingRelationship.EXCLUDED,
        source_requirement_ids=("URS-001",),
        source_pages=(3,),
        rationale="Out of scope for DQ",
    )
    response = DQMapping(
        mapping_id="MAP-002",
        relationship=MappingRelationship.USER_RESPONSE,
        source_requirement_ids=("URS-002",),
        dq_section_ids=("DQ-1", "DQ-2"),
        source_pages=(4,),
        dq_response=DQResponse("RESP-001", "User-authored DQ response", "qa"),
    )

    assert excluded.relationship is MappingRelationship.EXCLUDED
    assert excluded.rationale == "Out of scope for DQ"
    assert response.dq_response is not None
    assert response.dq_response.text == "User-authored DQ response"
