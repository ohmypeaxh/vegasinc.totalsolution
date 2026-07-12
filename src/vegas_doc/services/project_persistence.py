"""Versioned DQ project JSON persistence."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any

from vegas_doc.models.common import ReviewStatus
from vegas_doc.models.dq_mapping import DQMapping, DQResponse, MappingRelationship
from vegas_doc.models.extraction import DocumentExtractionResult, DocumentKind, ExtractionMethod, PageExtractionMetadata
from vegas_doc.models.ocr import OCRPageError, OCRPageResult, OCRResult
from vegas_doc.models.project import DQProject, PROJECT_SCHEMA_VERSION, SUPPORTED_PROJECT_SCHEMA_VERSIONS, ProjectInfo, TemplateSettings
from vegas_doc.models.urs import RequirementPriority, URSRequirement, VerificationMethod


class ProjectPersistenceError(Exception):
    """Base project persistence exception."""


class ProjectAlreadyExistsError(ProjectPersistenceError):
    """Raised when saving would overwrite an existing project without permission."""


class MalformedProjectError(ProjectPersistenceError):
    """Raised when a project file cannot be decoded or validated."""


class UnsupportedProjectVersionError(ProjectPersistenceError):
    """Raised when a project file uses an unsupported schema version."""


class DQProjectRepository:
    """UTF-8 JSON repository with atomic writes and explicit version checks."""

    def save(self, project: DQProject, path: Path, overwrite: bool = False) -> None:
        """Save a project atomically, protecting existing files unless allowed."""

        if path.exists() and not overwrite:
            raise ProjectAlreadyExistsError(f"Project already exists: {path}")
        project.assert_no_secret_fields()
        payload = _project_to_dict(project)
        path.parent.mkdir(parents=True, exist_ok=True)
        temp_name: str | None = None
        try:
            with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False, suffix=".tmp") as temp_file:
                temp_name = temp_file.name
                json.dump(payload, temp_file, ensure_ascii=False, indent=2)
                temp_file.write("\n")
                temp_file.flush()
                os.fsync(temp_file.fileno())
            Path(temp_name).replace(path)
        except Exception as error:
            if temp_name is not None:
                Path(temp_name).unlink(missing_ok=True)
            if isinstance(error, ProjectPersistenceError):
                raise
            raise ProjectPersistenceError(f"Failed to save project {path}: {error}") from error

    def load(self, path: Path) -> DQProject:
        """Load and validate a versioned DQ project file."""

        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as error:
            raise MalformedProjectError(f"Malformed project JSON: {path}") from error
        except OSError as error:
            raise ProjectPersistenceError(f"Failed to read project {path}: {error}") from error
        if not isinstance(payload, dict):
            raise MalformedProjectError("Project payload must be a JSON object")
        version = payload.get("schema_version")
        if version not in SUPPORTED_PROJECT_SCHEMA_VERSIONS:
            raise UnsupportedProjectVersionError(f"Unsupported DQ project schema version: {version}")
        try:
            return _project_from_dict(payload)
        except (KeyError, TypeError, ValueError) as error:
            raise MalformedProjectError(f"Malformed project payload: {error}") from error


def _path_to_str(path: Path | None) -> str | None:
    return str(path) if path is not None else None


def _path_from_str(value: str | None) -> Path | None:
    return Path(value) if value else None


def _project_to_dict(project: DQProject) -> dict[str, Any]:
    return {
        "schema_version": project.schema_version,
        "project_info": {
            "project_id": project.project_info.project_id,
            "name": project.project_info.name,
            "created_at": project.project_info.created_at,
            "updated_at": project.project_info.updated_at,
        },
        "source_references": [str(path) for path in project.source_references],
        "extraction_results": [_extraction_to_dict(item) for item in project.extraction_results],
        "ocr_metadata": _ocr_to_dict(project.ocr_metadata) if project.ocr_metadata else None,
        "requirements": [_requirement_to_dict(item) for item in project.requirements],
        "corrections": dict(project.corrections),
        "classifications": dict(project.classifications),
        "mappings": [_mapping_to_dict(item) for item in project.mappings],
        "review_status": project.review_status.value,
        "template_settings": {
            "template_path": _path_to_str(project.template_settings.template_path),
            "output_directory": _path_to_str(project.template_settings.output_directory),
        },
    }


def _project_from_dict(data: dict[str, Any]) -> DQProject:
    info = data["project_info"]
    template = data.get("template_settings") or {}
    return DQProject(
        schema_version=data.get("schema_version", PROJECT_SCHEMA_VERSION),
        project_info=ProjectInfo(info["project_id"], info["name"], info.get("created_at"), info.get("updated_at")),
        source_references=tuple(Path(path) for path in data.get("source_references", [])),
        extraction_results=tuple(_extraction_from_dict(item) for item in data.get("extraction_results", [])),
        ocr_metadata=_ocr_from_dict(data["ocr_metadata"]) if data.get("ocr_metadata") else None,
        requirements=tuple(_requirement_from_dict(item) for item in data.get("requirements", [])),
        corrections=dict(data.get("corrections", {})),
        classifications=dict(data.get("classifications", {})),
        mappings=tuple(_mapping_from_dict(item) for item in data.get("mappings", [])),
        review_status=ReviewStatus(data.get("review_status", ReviewStatus.NOT_REVIEWED.value)),
        template_settings=TemplateSettings(_path_from_str(template.get("template_path")), _path_from_str(template.get("output_directory"))),
    )


def _extraction_to_dict(result: DocumentExtractionResult) -> dict[str, Any]:
    return {
        "source_path": str(result.source_path),
        "document_kind": result.document_kind.value,
        "pages": [
            {
                "source_path": str(page.source_path),
                "page_number": page.page_number,
                "document_kind": page.document_kind.value,
                "extraction_method": page.extraction_method.value,
                "original_text": page.original_text,
                "normalized_text": page.normalized_text,
                "reviewed_text": page.reviewed_text,
                "confidence": page.confidence,
                "warnings": list(page.warnings),
                "errors": list(page.errors),
                "trace_id": page.trace_id,
            }
            for page in result.pages
        ],
    }


def _extraction_from_dict(data: dict[str, Any]) -> DocumentExtractionResult:
    return DocumentExtractionResult(
        source_path=Path(data["source_path"]),
        document_kind=DocumentKind(data["document_kind"]),
        pages=tuple(
            PageExtractionMetadata(
                source_path=Path(page["source_path"]),
                page_number=page["page_number"],
                document_kind=DocumentKind(page["document_kind"]),
                extraction_method=ExtractionMethod(page["extraction_method"]),
                original_text=page.get("original_text", ""),
                normalized_text=page.get("normalized_text"),
                reviewed_text=page.get("reviewed_text"),
                confidence=page.get("confidence"),
                warnings=tuple(page.get("warnings", [])),
                errors=tuple(page.get("errors", [])),
                trace_id=page.get("trace_id"),
            )
            for page in data.get("pages", [])
        ),
    )


def _ocr_to_dict(result: OCRResult) -> dict[str, Any]:
    return {
        "pages": [
            {
                "page_number": page.page_number,
                "text": page.text,
                "confidence": page.confidence,
                "warnings": list(page.warnings),
                "provider_metadata": page.provider_metadata,
            }
            for page in result.pages
        ],
        "errors": [
            {"page_number": error.page_number, "code": error.code, "message": error.message, "retryable": error.retryable}
            for error in result.errors
        ],
        "cancelled": result.cancelled,
    }


def _ocr_from_dict(data: dict[str, Any]) -> OCRResult:
    return OCRResult(
        pages=tuple(OCRPageResult(page["page_number"], page.get("text", ""), page.get("confidence"), tuple(page.get("warnings", [])), dict(page.get("provider_metadata", {}))) for page in data.get("pages", [])),
        errors=tuple(OCRPageError(error["page_number"], error.get("code", "unknown"), error.get("message", ""), error.get("retryable", False)) for error in data.get("errors", [])),
        cancelled=bool(data.get("cancelled", False)),
    )


def _requirement_to_dict(requirement: URSRequirement) -> dict[str, Any]:
    return {
        "requirement_id": requirement.requirement_id,
        "source_document": str(requirement.source_document),
        "source_page": requirement.source_page,
        "source_section": requirement.source_section,
        "original_text": requirement.original_text,
        "normalized_text": requirement.normalized_text,
        "category": requirement.category,
        "subcategory": requirement.subcategory,
        "priority": requirement.priority.value,
        "verification_method": requirement.verification_method.value,
        "dq_section": requirement.dq_section,
        "confidence": requirement.confidence,
        "included": requirement.included,
        "user_reviewed": requirement.user_reviewed,
        "user_notes": requirement.user_notes,
    }


def _requirement_from_dict(data: dict[str, Any]) -> URSRequirement:
    return URSRequirement(
        requirement_id=data["requirement_id"],
        source_document=Path(data["source_document"]),
        source_page=data["source_page"],
        source_section=data.get("source_section"),
        original_text=data["original_text"],
        normalized_text=data["normalized_text"],
        category=data.get("category"),
        subcategory=data.get("subcategory"),
        priority=RequirementPriority(data.get("priority", RequirementPriority.UNSPECIFIED.value)),
        verification_method=VerificationMethod(data.get("verification_method", VerificationMethod.UNSPECIFIED.value)),
        dq_section=data.get("dq_section"),
        confidence=data.get("confidence"),
        included=bool(data.get("included", True)),
        user_reviewed=bool(data.get("user_reviewed", False)),
        user_notes=data.get("user_notes"),
    )


def _mapping_to_dict(mapping: DQMapping) -> dict[str, Any]:
    return {
        "mapping_id": mapping.mapping_id,
        "relationship": mapping.relationship.value,
        "source_requirement_ids": list(mapping.source_requirement_ids),
        "dq_section_ids": list(mapping.dq_section_ids),
        "source_pages": list(mapping.source_pages),
        "dq_response": None if mapping.dq_response is None else {"response_id": mapping.dq_response.response_id, "text": mapping.dq_response.text, "author": mapping.dq_response.author},
        "review_status": mapping.review_status.value,
        "rationale": mapping.rationale,
    }


def _mapping_from_dict(data: dict[str, Any]) -> DQMapping:
    response = data.get("dq_response")
    return DQMapping(
        mapping_id=data["mapping_id"],
        relationship=MappingRelationship(data["relationship"]),
        source_requirement_ids=tuple(data.get("source_requirement_ids", [])),
        dq_section_ids=tuple(data.get("dq_section_ids", [])),
        source_pages=tuple(data.get("source_pages", [])),
        dq_response=DQResponse(response["response_id"], response.get("text", ""), response.get("author")) if response else None,
        review_status=ReviewStatus(data.get("review_status", ReviewStatus.NOT_REVIEWED.value)),
        rationale=data.get("rationale"),
    )
