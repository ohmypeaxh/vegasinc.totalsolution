"""URS parsing, classification, DQ suggestions, and validation services."""

from __future__ import annotations

import re
from dataclasses import replace
from pathlib import Path

from vegas_doc.models.dq_mapping import DQMapping, DQResponse, MappingRelationship
from vegas_doc.models.extraction import DocumentExtractionResult
from vegas_doc.models.urs import RequirementPriority, URSRequirement, VerificationMethod

_REQUIREMENT_WORDS = re.compile(r"\b(shall|must|should|required|requires?)\b|해야\s*한다|하여야\s*한다|필수|요구|되어야\s*한다", re.I)
_ID_PATTERN = re.compile(r"\b(?:URS[-_\s]?)?(\d{1,4}(?:\.\d+)*)\b", re.I)
_HEADING_WORDS = re.compile(r"^(table of contents|contents|목차|revision|개정|chapter|section)\b", re.I)

DEFAULT_CATEGORY_KEYWORDS: dict[str, tuple[str, ...]] = {
    "Safety": ("safety", "alarm", "interlock", "emergency", "안전", "알람", "인터록"),
    "Control": ("control", "plc", "sequence", "자동", "제어"),
    "Data": ("data", "record", "audit", "report", "데이터", "기록"),
    "Performance": ("performance", "speed", "capacity", "accuracy", "성능", "속도", "정확"),
    "Interface": ("interface", "screen", "hmi", "communication", "화면", "통신"),
}

CATEGORY_SECTIONS: dict[str, str] = {
    "Safety": "Safety and Interlocks",
    "Control": "Control Design",
    "Data": "Data Integrity",
    "Performance": "Performance Design",
    "Interface": "Interfaces",
    "General": "General Design",
}


class DefaultURSParser:
    """Deterministic default URS parser for English/Korean requirement text."""

    def parse(self, extraction: DocumentExtractionResult) -> tuple[URSRequirement, ...]:
        requirements: list[URSRequirement] = []
        seen: dict[str, int] = {}
        for page in extraction.pages:
            blocks = _candidate_blocks(page.reviewed_text or page.normalized_text or page.original_text)
            for block in blocks:
                if _HEADING_WORDS.search(block) or not _REQUIREMENT_WORDS.search(block):
                    continue
                requirement_id = _extract_requirement_id(block, len(requirements) + 1)
                seen[requirement_id] = seen.get(requirement_id, 0) + 1
                unique_id = requirement_id if seen[requirement_id] == 1 else f"{requirement_id}-DUP{seen[requirement_id]}"
                requirements.append(
                    URSRequirement(
                        requirement_id=unique_id,
                        source_document=page.source_path,
                        source_page=page.page_number,
                        source_section=None,
                        original_text=block,
                        normalized_text=_clean_requirement_text(block),
                        confidence=page.confidence,
                    )
                )
        return tuple(requirements)


class KeywordRequirementClassifier:
    """Configurable keyword classifier that preserves user overrides."""

    def __init__(self, keywords: dict[str, tuple[str, ...]] | None = None) -> None:
        self._keywords = keywords or DEFAULT_CATEGORY_KEYWORDS

    def classify(self, requirement: URSRequirement, overrides: dict[str, str] | None = None) -> URSRequirement:
        """Return a classified requirement, respecting explicit overrides."""

        overrides = overrides or {}
        category = overrides.get(requirement.requirement_id) or self._match_category(requirement.normalized_text)
        return replace(requirement, category=category, dq_section=CATEGORY_SECTIONS.get(category, CATEGORY_SECTIONS["General"]), verification_method=_verification_for(category), priority=_priority_for(category))

    def _match_category(self, text: str) -> str:
        lowered = text.lower()
        for category, keywords in self._keywords.items():
            if any(keyword.lower() in lowered for keyword in keywords):
                return category
        return "General"


class DQSuggestionService:
    """Generate deterministic editable DQ response suggestions."""

    def suggest(self, requirement: URSRequirement, existing: DQResponse | None = None, user_edited: bool = False) -> DQResponse:
        """Return an existing user edit unchanged, otherwise a deterministic suggestion."""

        if existing is not None and user_edited:
            return existing
        category = requirement.category or "General"
        section = requirement.dq_section or CATEGORY_SECTIONS.get(category, CATEGORY_SECTIONS["General"])
        text = f"The design shall address {requirement.requirement_id} in the {section} section: {requirement.normalized_text}"
        return DQResponse(f"RESP-{requirement.requirement_id}", text)


class DQProjectValidator:
    """Aggregate validation before DQ document generation."""

    def validate_for_generation(self, project_name: str, requirements: tuple[URSRequirement, ...], mappings: tuple[DQMapping, ...], template_path: Path, output_path: Path) -> list[str]:
        """Return Korean user-facing validation messages."""

        errors: list[str] = []
        if not project_name.strip():
            errors.append("프로젝트명을 입력해 주세요.")
        included = [item for item in requirements if item.included]
        if not included:
            errors.append("검토 대상 URS 요구사항이 없습니다.")
        if any(not item.user_reviewed for item in included):
            errors.append("포함된 모든 요구사항을 검토 완료로 표시해 주세요.")
        mapped_ids = {req_id for mapping in mappings for req_id in mapping.source_requirement_ids}
        if any(item.requirement_id not in mapped_ids for item in included):
            errors.append("모든 포함 요구사항에 DQ 응답 매핑이 필요합니다.")
        if not template_path.exists():
            errors.append("유효한 Word 템플릿을 선택해 주세요.")
        if not output_path.name or output_path.suffix.lower() != ".docx":
            errors.append("출력 파일명은 .docx 형식이어야 합니다.")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        return errors


def build_mappings(requirements: tuple[URSRequirement, ...], responses: dict[str, DQResponse]) -> tuple[DQMapping, ...]:
    """Create one-to-one mappings for included requirements with responses."""

    mappings: list[DQMapping] = []
    for requirement in requirements:
        if not requirement.included:
            mappings.append(DQMapping(f"MAP-{requirement.requirement_id}", MappingRelationship.EXCLUDED, (requirement.requirement_id,), source_pages=(requirement.source_page,), rationale="User excluded"))
            continue
        response = responses.get(requirement.requirement_id)
        if response is None:
            continue
        mappings.append(DQMapping(f"MAP-{requirement.requirement_id}", MappingRelationship.ONE_TO_ONE, (requirement.requirement_id,), (requirement.dq_section or "DQ",), (requirement.source_page,), response))
    return tuple(mappings)


def _candidate_blocks(text: str) -> list[str]:
    blocks: list[str] = []
    current: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.strip(" \t•*-|")
        if not line:
            if current:
                blocks.append(" ".join(current))
                current = []
            continue
        if _ID_PATTERN.search(line) and current:
            blocks.append(" ".join(current))
            current = [line]
        else:
            current.append(line)
    if current:
        blocks.append(" ".join(current))
    return blocks


def _extract_requirement_id(text: str, fallback: int) -> str:
    match = re.search(r"\bURS[-_\s]?(\d{1,4}(?:\.\d+)*)\b", text, re.I)
    if match:
        return f"URS-{match.group(1).replace('.', '-') }"
    numeric = _ID_PATTERN.search(text)
    if numeric:
        return f"URS-{numeric.group(1).replace('.', '-') }"
    return f"URS-AUTO-{fallback:03d}"


def _clean_requirement_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _verification_for(category: str) -> VerificationMethod:
    return VerificationMethod.TEST if category in {"Safety", "Performance", "Control"} else VerificationMethod.INSPECTION


def _priority_for(category: str) -> RequirementPriority:
    return RequirementPriority.HIGH if category == "Safety" else RequirementPriority.MEDIUM
