"""Domain models for Raw Data Word document generation."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class RawDataType(str, Enum):
    """Supported Raw Data template layouts."""

    HEPA_FILTER = "HEPA Filter"
    TWO_CUT_COMMENT = "2 cut Picture (comment)"
    TWO_CUT_NON_COMMENT = "2 cut Picture (non-comment)"

    @property
    def uses_pictures(self) -> bool:
        """Return whether this layout renders the ordered picture list."""

        return self is not RawDataType.HEPA_FILTER

    @property
    def includes_picture_names(self) -> bool:
        """Return whether picture captions contain file names."""

        return self is RawDataType.TWO_CUT_COMMENT


class QualificationType(str, Enum):
    """Qualification titles supported by Raw Data templates."""

    FACTORY_ACCEPTANCE_TEST = "FACTORY ACCEPTANCE TEST"
    INSTALLATION_QUALIFICATION = "INSTALLATION QUALIFICATION"
    OPERATIONAL_QUALIFICATION = "OPERATIONAL QUALIFICATION"
    INSTALLATION_AND_OPERATIONAL_QUALIFICATION = "INSTALLATION & OPERATIONAL QUALIFICATION"


@dataclass(frozen=True, slots=True)
class RawDataDocumentRequest:
    """Validated inputs required to generate one Raw Data DOCX file."""

    template_path: Path
    logo_path: Path
    output_directory: Path
    raw_data_type: RawDataType
    qualification_type: QualificationType
    document_number: str
    hepa_filter_count: int = 1
    verification_name: str = ""
    image_paths: tuple[Path, ...] = ()

    def output_filename(self) -> str:
        """Return a filesystem-safe deterministic output filename."""

        name = re.sub(r'[\\/:*?"<>|]+', "_", self.document_number.strip())
        return f"{name or 'Raw_Data'}_Raw_Data.docx"

    def validation_errors(self) -> tuple[str, ...]:
        """Return all user-correctable request errors."""

        errors: list[str] = []
        if not self.document_number.strip():
            errors.append("문서번호를 입력해 주세요.")
        if self.template_path.suffix.lower() != ".docx" or not self.template_path.is_file():
            errors.append("유효한 Word DOCX 템플릿을 선택해 주세요.")
        if self.logo_path.suffix.lower() not in _IMAGE_EXTENSIONS or not self.logo_path.is_file():
            errors.append("유효한 회사 로고 이미지 파일을 선택해 주세요.")
        if self.output_directory == Path() or not self.output_directory.is_dir():
            errors.append("유효한 Word 저장 폴더를 선택해 주세요.")
        if self.raw_data_type is RawDataType.HEPA_FILTER:
            if self.hepa_filter_count < 1:
                errors.append("HEPA FILTER 개수는 1개 이상이어야 합니다.")
        else:
            if not self.image_paths:
                errors.append("첨부할 사진을 한 장 이상 추가해 주세요.")
            for image_path in self.image_paths:
                if image_path.suffix.lower() not in _IMAGE_EXTENSIONS or not image_path.is_file():
                    errors.append(f"유효하지 않은 첨부사진입니다: {image_path}")
        return tuple(errors)


_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff"}
