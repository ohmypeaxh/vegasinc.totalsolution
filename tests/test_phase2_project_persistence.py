"""Phase 2 versioned DQ project persistence tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from vegas_doc.models.common import ReviewStatus
from vegas_doc.models.dq_mapping import DQMapping, MappingRelationship
from vegas_doc.models.extraction import DocumentExtractionResult, DocumentKind, ExtractionMethod, PageExtractionMetadata
from vegas_doc.models.ocr import OCRPageError, OCRPageResult, OCRResult
from vegas_doc.models.project import DQProject, PROJECT_SCHEMA_VERSION, ProjectInfo, TemplateSettings
from vegas_doc.models.urs import URSRequirement
from vegas_doc.services.project_persistence import (
    DQProjectRepository,
    MalformedProjectError,
    ProjectAlreadyExistsError,
    ProjectPersistenceError,
    UnsupportedProjectVersionError,
)


def build_project(tmp_path: Path) -> DQProject:
    """Create a representative project without secrets or real user directories."""

    source = tmp_path / "URS.pdf"
    requirement = URSRequirement("URS-001", source, 1, "6.1", "Original requirement", "Normalized requirement")
    extraction = DocumentExtractionResult(
        source_path=source,
        document_kind=DocumentKind.MIXED_PDF,
        pages=(
            PageExtractionMetadata(
                source_path=source,
                page_number=1,
                document_kind=DocumentKind.MIXED_PDF,
                extraction_method=ExtractionMethod.EMBEDDED_TEXT,
                original_text="Original requirement",
                normalized_text="Normalized requirement",
                confidence=0.95,
                trace_id="page-1",
            ),
        ),
    )
    mapping = DQMapping(
        mapping_id="MAP-001",
        relationship=MappingRelationship.ONE_TO_ONE,
        source_requirement_ids=("URS-001",),
        dq_section_ids=("DQ-1",),
        source_pages=(1,),
    )
    return DQProject(
        schema_version=PROJECT_SCHEMA_VERSION,
        project_info=ProjectInfo("PRJ-001", "Test Project"),
        source_references=(source,),
        extraction_results=(extraction,),
        ocr_metadata=OCRResult(pages=(OCRPageResult(1, "ocr text", 0.9),), errors=(OCRPageError(2, "timeout", "failed", True),)),
        requirements=(requirement,),
        corrections={"URS-001": "Corrected text"},
        classifications={"URS-001": "safety"},
        mappings=(mapping,),
        review_status=ReviewStatus.NEEDS_REVIEW,
        template_settings=TemplateSettings(tmp_path / "template.docx", tmp_path / "out"),
    )


def test_project_save_and_reopen_round_trip(tmp_path) -> None:
    """Projects save and load with traceability preserved."""

    repository = DQProjectRepository()
    path = tmp_path / "project.vdq.json"
    project = build_project(tmp_path)

    repository.save(project, path)
    reopened = repository.load(path)

    assert reopened.schema_version == PROJECT_SCHEMA_VERSION
    assert reopened.project_info.project_id == "PRJ-001"
    assert reopened.requirements[0].original_text == "Original requirement"
    assert reopened.extraction_results[0].pages[0].trace_id == "page-1"
    assert reopened.mappings[0].source_requirement_ids == ("URS-001",)
    assert reopened.ocr_metadata is not None
    assert reopened.ocr_metadata.errors[0].retryable


def test_project_save_protects_existing_file(tmp_path) -> None:
    """Save does not silently overwrite existing project files."""

    repository = DQProjectRepository()
    path = tmp_path / "project.vdq.json"
    repository.save(build_project(tmp_path), path)

    with pytest.raises(ProjectAlreadyExistsError):
        repository.save(build_project(tmp_path), path)


def test_project_atomic_write_failure_does_not_corrupt_existing_file(tmp_path, monkeypatch) -> None:
    """A failed atomic replace leaves the existing file unchanged."""

    repository = DQProjectRepository()
    path = tmp_path / "project.vdq.json"
    repository.save(build_project(tmp_path), path)
    original = path.read_text(encoding="utf-8")

    def fail_replace(self, target):  # type: ignore[no-untyped-def]
        raise OSError("replace failed")

    monkeypatch.setattr(Path, "replace", fail_replace)

    with pytest.raises(ProjectPersistenceError):
        repository.save(build_project(tmp_path), path, overwrite=True)

    assert path.read_text(encoding="utf-8") == original


def test_project_load_rejects_malformed_file(tmp_path) -> None:
    """Malformed JSON raises a domain-specific error."""

    path = tmp_path / "bad.vdq.json"
    path.write_text("{bad json", encoding="utf-8")

    with pytest.raises(MalformedProjectError):
        DQProjectRepository().load(path)


def test_project_load_rejects_unsupported_version(tmp_path) -> None:
    """Unsupported schema versions are rejected explicitly."""

    path = tmp_path / "old.vdq.json"
    path.write_text(json.dumps({"schema_version": "1.0"}), encoding="utf-8")

    with pytest.raises(UnsupportedProjectVersionError):
        DQProjectRepository().load(path)


def test_project_save_rejects_secret_like_fields(tmp_path) -> None:
    """Project JSON persistence refuses secret-looking dynamic fields."""

    project = DQProject(
        schema_version=PROJECT_SCHEMA_VERSION,
        project_info=ProjectInfo("PRJ-SECRET", "Secret Test"),
        corrections={"api_key": "should-not-save"},
    )

    with pytest.raises(ValueError, match="Secret-like"):
        DQProjectRepository().save(project, tmp_path / "secret.vdq.json")
