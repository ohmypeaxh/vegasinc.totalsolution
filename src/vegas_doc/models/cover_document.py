"""Cover Generator request model and qualification title mappings."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


QUALIFICATION_TITLES: dict[str, tuple[str, str]] = {
    "URS": ("사용자 요구규격서", "User Requirement Specification"),
    "F&DS": ("기능 및 설계 규격서", "Functional & Design Specification"),
    "DQ": ("설계적격성평가", "Design Qualification"),
    "FAT": ("공장적합성시험", "Factory Acceptance Test"),
    "SAT": ("제조소적합성시험", "Site Acceptance Test"),
    "IQ": ("설치적격성평가", "Installation Qualification"),
    "OQ": ("운전적격성평가", "Operational Qualification"),
    "IOQ": ("설치 및 운전적격성평가", "Installation & Operational Qualification"),
    "PQ": ("성능적격성평가", "Performance Qualification"),
    "CD": ("과산화수소증기 사이클 개발", "Cycle Development"),
    "CV": ("과산화수소증기 사이클 검증", "Cycle Validation"),
}

TEXT_PLACEHOLDERS = (
    "##장비명##",
    "##적격성평가축약##",
    "##적격성평가한글##",
    "##적격성평가영문##",
    "##계획서번호##",
    "##보고서번호##",
    "##해당년도##",
)
LOGO_PLACEHOLDERS = tuple(f"##고객사로고{index}##" for index in range(1, 6))
REQUIRED_COVER_SHEETS = ("개별표지", "개별라벨")


@dataclass(frozen=True, slots=True)
class CoverDocumentRequest:
    """Validated inputs for creating a two-page cover PDF from Excel."""

    template_path: Path
    customer_logo_path: Path
    output_directory: Path
    equipment_name: str
    qualification_abbreviation: str
    plan_number: str
    report_number: str
    applicable_year: str

    def replacements(self) -> dict[str, str]:
        """Return all text placeholder replacements for the Excel template."""

        korean, english = QUALIFICATION_TITLES[self.qualification_abbreviation]
        return {
            "##장비명##": self.equipment_name.strip(),
            "##적격성평가축약##": self.qualification_abbreviation,
            "##적격성평가한글##": korean,
            "##적격성평가영문##": english,
            "##계획서번호##": self.plan_number.strip(),
            "##보고서번호##": self.report_number.strip(),
            "##해당년도##": self.applicable_year.strip(),
        }

    def output_filename(self) -> str:
        """Return the requested filesystem-safe cover PDF name."""

        equipment = re.sub(r'[\\/:*?"<>|]+', "_", self.equipment_name.strip())
        return f"{equipment}_{self.qualification_abbreviation}_cover.pdf"

    def validation_errors(self) -> tuple[str, ...]:
        """Return actionable validation errors without mutating the request."""

        errors: list[str] = []
        equipment = self.equipment_name.strip()
        if not equipment:
            errors.append("장비명을 입력해 주세요.")
        elif not equipment.isascii() or not re.search(r"[A-Za-z]", equipment):
            errors.append("장비명은 영문으로 작성해 주세요.")
        if self.qualification_abbreviation not in QUALIFICATION_TITLES:
            errors.append("적격성평가 종류를 선택해 주세요.")
        if not self.plan_number.strip():
            errors.append("계획서번호를 입력해 주세요.")
        if not self.report_number.strip():
            errors.append("보고서번호를 입력해 주세요.")
        if not self.applicable_year.strip():
            errors.append("해당년도를 입력해 주세요.")
        if self.template_path.suffix.lower() != ".xlsx" or not self.template_path.is_file():
            errors.append("유효한 Excel XLSX 템플릿을 선택해 주세요.")
        if self.customer_logo_path.suffix.lower() not in _IMAGE_EXTENSIONS or not self.customer_logo_path.is_file():
            errors.append("유효한 고객사 로고 이미지를 선택해 주세요.")
        if not self.output_directory.is_dir():
            errors.append("유효한 PDF 저장 폴더를 선택해 주세요.")
        return tuple(errors)


_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff"}
