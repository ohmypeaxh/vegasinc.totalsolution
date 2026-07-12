"""DQ document input model used by the UI and generation services."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path

_INVALID_WINDOWS_FILENAME = re.compile(r'[\\/:*?"<>|]')
_SECTION_NUMBER = re.compile(r"^\d+(?:\.\d+)*$")


@dataclass(frozen=True, slots=True)
class DQDocumentData:
    """Validated non-secret DQ document metadata and source paths."""

    logo_path: Path
    template_path: Path
    urs_pdf_path: Path
    document_number: str
    version_number: str
    equipment_name: str
    author_name: str
    author_date: date
    author_position: str
    vendor_name: str
    start_requirement: str
    end_requirement: str
    output_directory: Path
    output_filename: str = ""

    def validation_errors(self, *, require_existing_files: bool = True) -> list[str]:
        errors: list[str] = []
        required_text = {
            "문서번호": self.document_number,
            "버전번호": self.version_number,
            "장비명": self.equipment_name,
            "작성자": self.author_name,
            "작성자 직위": self.author_position,
            "업체명": self.vendor_name,
            "시작 요구사항 번호": self.start_requirement,
            "종료 요구사항 번호": self.end_requirement,
        }
        errors.extend(f"{label} 항목은 필수입니다." for label, value in required_text.items() if not value.strip())
        for label, path, extensions in (
            ("회사 로고", self.logo_path, {".png", ".jpg", ".jpeg"}),
            ("Word 템플릿", self.template_path, {".docx"}),
            ("URS PDF", self.urs_pdf_path, {".pdf"}),
        ):
            if path.suffix.lower() not in extensions:
                errors.append(f"{label} 파일 형식이 올바르지 않습니다.")
            elif require_existing_files and not path.is_file():
                errors.append(f"{label} 파일을 찾을 수 없습니다: {path}")
        if not _SECTION_NUMBER.fullmatch(self.start_requirement.strip()):
            errors.append("시작 요구사항 번호 형식이 올바르지 않습니다.")
        if not _SECTION_NUMBER.fullmatch(self.end_requirement.strip()):
            errors.append("종료 요구사항 번호 형식이 올바르지 않습니다.")
        if _SECTION_NUMBER.fullmatch(self.start_requirement.strip()) and _SECTION_NUMBER.fullmatch(self.end_requirement.strip()):
            if section_key(self.start_requirement) > section_key(self.end_requirement):
                errors.append("시작 요구사항 번호는 종료 번호보다 클 수 없습니다.")
        if require_existing_files and (not self.output_directory.exists() or not self.output_directory.is_dir()):
            errors.append(f"저장 폴더를 찾을 수 없습니다: {self.output_directory}")
        return errors

    def resolved_output_filename(self) -> str:
        requested = self.output_filename.strip()
        if not requested:
            requested = f"{self.document_number}_{self.equipment_name}_DQ_{self.author_date:%Y-%m-%d}.docx"
        safe = _INVALID_WINDOWS_FILENAME.sub("_", requested).strip(" .")
        if not safe.lower().endswith(".docx"):
            safe += ".docx"
        return safe

    def output_path(self) -> Path:
        return self.output_directory / self.resolved_output_filename()


def section_key(value: str) -> tuple[int, ...]:
    """Compare hierarchical section numbers numerically, so 6.10 follows 6.9."""

    if not _SECTION_NUMBER.fullmatch(value.strip()):
        raise ValueError(f"Invalid section number: {value}")
    return tuple(int(part) for part in value.strip().split("."))
