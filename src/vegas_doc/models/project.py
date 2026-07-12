"""Versioned DQ project persistence models."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from vegas_doc.models.common import ReviewStatus
from vegas_doc.models.dq_mapping import DQMapping
from vegas_doc.models.extraction import DocumentExtractionResult
from vegas_doc.models.ocr import OCRResult
from vegas_doc.models.urs import URSRequirement

PROJECT_SCHEMA_VERSION = "2.0"
SUPPORTED_PROJECT_SCHEMA_VERSIONS = frozenset({PROJECT_SCHEMA_VERSION})


@dataclass(frozen=True, slots=True)
class ProjectInfo:
    """Human-readable project metadata without secrets."""

    project_id: str
    name: str
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str | None = None

    def __post_init__(self) -> None:
        if not self.project_id.strip():
            raise ValueError("project_id is required")
        if not self.name.strip():
            raise ValueError("name is required")


@dataclass(frozen=True, slots=True)
class TemplateSettings:
    """Future template/output settings containing paths only, never secrets."""

    template_path: Path | None = None
    output_directory: Path | None = None


@dataclass(frozen=True, slots=True)
class DQProject:
    """Versioned project aggregate for future DQ generation traceability."""

    schema_version: str
    project_info: ProjectInfo
    source_references: tuple[Path, ...] = ()
    extraction_results: tuple[DocumentExtractionResult, ...] = ()
    ocr_metadata: OCRResult | None = None
    requirements: tuple[URSRequirement, ...] = ()
    corrections: dict[str, str] = field(default_factory=dict)
    classifications: dict[str, str] = field(default_factory=dict)
    mappings: tuple[DQMapping, ...] = ()
    review_status: ReviewStatus = ReviewStatus.NOT_REVIEWED
    template_settings: TemplateSettings = field(default_factory=TemplateSettings)

    def __post_init__(self) -> None:
        if self.schema_version not in SUPPORTED_PROJECT_SCHEMA_VERSIONS:
            raise ValueError(f"Unsupported DQ project schema version: {self.schema_version}")

    def assert_no_secret_fields(self) -> None:
        """Reject accidental secret-looking fields before persistence."""

        def scan(value: Any, path: str = "project") -> None:
            if isinstance(value, dict):
                for key, child in value.items():
                    lowered = str(key).lower()
                    if any(token in lowered for token in ("secret", "password", "token", "api_key", "apikey")):
                        raise ValueError(f"Secret-like field is not allowed: {path}.{key}")
                    scan(child, f"{path}.{key}")
            elif isinstance(value, (list, tuple)):
                for index, child in enumerate(value):
                    scan(child, f"{path}[{index}]")

        scan(self.corrections, "corrections")
        scan(self.classifications, "classifications")
