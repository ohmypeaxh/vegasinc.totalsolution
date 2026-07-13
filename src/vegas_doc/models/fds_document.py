"""Domain models for F&DS requirement transformation and Word output."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from vegas_doc.models.dq_document_data import section_key
from vegas_doc.utils.date_format import format_document_date


@dataclass(frozen=True, slots=True)
class FDSTransformationRule:
    """Replace one URS sentence ending with an F&DS design sentence ending."""

    source_ending: str
    target_ending: str

    def __post_init__(self) -> None:
        if not self.source_ending.strip() or not self.target_ending.strip():
            raise ValueError("F&DS transformation rule endings cannot be empty")


@dataclass(frozen=True, slots=True)
class FDSStatement:
    """Traceable original URS sentence and editable F&DS sentence."""

    requirement_id: str
    source_page: int
    original_text: str
    generated_text: str


@dataclass(frozen=True, slots=True)
class FDSDocumentRequest:
    """Reviewed data required to generate one F&DS Word document."""

    template_path: Path
    source_pdf_path: Path
    logo_path: Path
    output_directory: Path
    equipment_name: str
    document_number: str
    write_date: date
    start_requirement: str
    end_requirement: str
    statements: tuple[FDSStatement, ...]

    def output_filename(self) -> str:
        """Return a safe, deterministic F&DS document filename."""

        name = f"{self.document_number}_{self.equipment_name}_FDS_{format_document_date(self.write_date)}"
        cleaned = re.sub(r'[\\/:*?"<>|]+', "_", name.strip())
        return f"{cleaned or 'FDS'}.docx"

    def validation_errors(self) -> tuple[str, ...]:
        """Return all user-correctable generation errors."""

        errors: list[str] = []
        if not self.equipment_name.strip():
            errors.append("장비명을 입력해 주세요.")
        if not self.document_number.strip():
            errors.append("문서번호를 입력해 주세요.")
        if self.source_pdf_path.suffix.lower() != ".pdf" or not self.source_pdf_path.is_file():
            errors.append("유효한 URS PDF 파일을 선택해 주세요.")
        if self.logo_path.suffix.lower() not in {".png", ".jpg", ".jpeg", ".bmp"} or not self.logo_path.is_file():
            errors.append("유효한 회사 로고 이미지 파일을 선택해 주세요.")
        if self.template_path.suffix.lower() != ".docx" or not self.template_path.is_file():
            errors.append("유효한 Word DOCX 템플릿을 선택해 주세요.")
        if self.output_directory == Path() or not self.output_directory.is_dir():
            errors.append("유효한 Word 저장 폴더를 선택해 주세요.")
        try:
            start = section_key(self.start_requirement)
            end = section_key(self.end_requirement)
            if start > end:
                errors.append("시작 요구사항 번호는 종료 번호보다 클 수 없습니다.")
        except ValueError:
            errors.append("시작 및 종료 요구사항 번호를 숫자 계층 형식으로 입력해 주세요. 예: 6.4")
        if not self.statements:
            errors.append("검토된 F&DS 변환 내용이 없습니다. URS 분석을 먼저 실행해 주세요.")
        if any(not item.generated_text.strip() for item in self.statements):
            errors.append("비어 있는 F&DS 변환 문장을 확인해 주세요.")
        return tuple(errors)
