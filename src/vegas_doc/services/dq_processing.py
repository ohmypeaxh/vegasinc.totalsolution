"""URS parsing, classification, DQ suggestions, and validation services."""

from __future__ import annotations

import re
from dataclasses import replace
from pathlib import Path

from vegas_doc.models.dq_mapping import DQMapping, DQResponse, MappingRelationship
from vegas_doc.models.extraction import DocumentExtractionResult
from vegas_doc.models.dq_document_data import section_key
from vegas_doc.models.urs import RequirementPriority, URSRequirement, VerificationMethod
from vegas_doc.services.numbered_text import numbered_text_blocks

_REQUIREMENT_WORDS = re.compile(r"\b(shall|must|should|required|requires?)\b|해야\s*한다|하여야\s*한다|필수|요구|되어야\s*한다", re.I)
_OBLIGATION_WORDS = re.compile(r"\b(shall|must|should|required|requires?)\b|해야\s*한다|하여야\s*한다|필수|되어야\s*한다", re.I)
_ID_PATTERN = re.compile(r"\b(?:URS[-_\s]?)?(\d{1,4}(?:\.\d+)*)\b", re.I)
_HEADING_WORDS = re.compile(r"^(table of contents|contents|목차|revision|개정|chapter|section)\b", re.I)
_SECTION_PREFIX = re.compile(r"^\s*(?P<number>\d+(?:\.\d+)*)(?:\s+|\s*[|:)\-]\s*)(?P<text>.+)$")

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

    def parse(
        self,
        extraction: DocumentExtractionResult,
        start_section: str | None = None,
        end_section: str | None = None,
    ) -> tuple[URSRequirement, ...]:
        """Parse traceable requirements, optionally within an inclusive numeric range."""

        if start_section and end_section:
            return self._parse_numbered_range(extraction, start_section, end_section)

        requirements: list[URSRequirement] = []
        seen: dict[str, int] = {}
        current_section: str | None = None
        heading_depth = max(len(section_key(start_section)), len(section_key(end_section))) if start_section and end_section else 1
        for page in extraction.pages:
            blocks = _candidate_blocks(page.reviewed_text or page.normalized_text or page.original_text)
            for block in blocks:
                section_match = _SECTION_PREFIX.match(block)
                section_number = section_match.group("number") if section_match else None
                if section_number and start_section and end_section and not section_in_range(section_number, start_section, end_section):
                    continue
                if _HEADING_WORDS.search(block):
                    continue
                is_range_heading = (
                    section_number is not None
                    and len(section_key(section_number)) <= heading_depth
                    and not _OBLIGATION_WORDS.search(block)
                    and not re.search(r"\bURS[-_\s]?\d+", block, re.I)
                )
                if section_match and (is_range_heading or (not _REQUIREMENT_WORDS.search(block) and not re.search(r"\bURS[-_\s]?\d+", block, re.I))):
                    current_section = _clean_requirement_text(block)
                    continue
                if not _REQUIREMENT_WORDS.search(block):
                    continue
                requirement_id = _extract_requirement_id(block, len(requirements) + 1)
                seen[requirement_id] = seen.get(requirement_id, 0) + 1
                unique_id = requirement_id if seen[requirement_id] == 1 else f"{requirement_id}-DUP{seen[requirement_id]}"
                source_section = current_section
                if source_section is None and section_number:
                    source_section = _parent_section(section_number)
                requirements.append(
                    URSRequirement(
                        requirement_id=unique_id,
                        source_document=page.source_path,
                        source_page=page.page_number,
                        source_section=source_section,
                        original_text=block,
                        normalized_text=_clean_requirement_text(block),
                        confidence=page.confidence,
                    )
                )
        return tuple(requirements)

    def _parse_numbered_range(
        self,
        extraction: DocumentExtractionResult,
        start_section: str,
        end_section: str,
    ) -> tuple[URSRequirement, ...]:
        """Parse table-style numbered rows, including specification phrases without verbs."""

        requirements: list[URSRequirement] = []
        seen: dict[str, int] = {}
        current_section: str | None = None
        heading_depth = max(len(section_key(start_section)), len(section_key(end_section)))
        for page in extraction.pages:
            text = page.reviewed_text or page.normalized_text or page.original_text
            for block in numbered_text_blocks(text, start_section, end_section):
                content = _clean_requirement_text(block.text)
                has_obligation = bool(_OBLIGATION_WORDS.search(content))
                if len(section_key(block.number)) <= heading_depth and not has_obligation:
                    current_section = f"{block.number} {content}".strip()
                    continue
                if not content:
                    continue
                seen[block.number] = seen.get(block.number, 0) + 1
                requirement_id = block.number if seen[block.number] == 1 else f"{block.number}-DUP{seen[block.number]}"
                requirements.append(
                    URSRequirement(
                        requirement_id=requirement_id,
                        source_document=page.source_path,
                        source_page=page.page_number,
                        source_section=current_section or _parent_section(block.number),
                        original_text=f"{block.number} {content}",
                        normalized_text=content,
                        confidence=page.confidence,
                    )
                )
        return tuple(requirements)


def section_in_range(value: str, start: str, end: str) -> bool:
    """Return whether a hierarchical number is in an inclusive section range."""

    value_key = section_key(value)
    start_key = section_key(start)
    end_key = section_key(end)
    return value_key >= start_key and (value_key <= end_key or value_key[: len(end_key)] == end_key)


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
        if not output_path.parent.is_dir():
            errors.append(f"저장 폴더를 찾을 수 없습니다: {output_path.parent}")
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
        return numeric.group(1)
    return f"URS-AUTO-{fallback:03d}"


def _clean_requirement_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _parent_section(section_number: str) -> str:
    parts = section_number.split(".")
    return ".".join(parts[:-1] if len(parts) > 1 else parts)


def _verification_for(category: str) -> VerificationMethod:
    return VerificationMethod.TEST if category in {"Safety", "Performance", "Control"} else VerificationMethod.INSPECTION


def _priority_for(category: str) -> RequirementPriority:
    return RequirementPriority.HIGH if category == "Safety" else RequirementPriority.MEDIUM
