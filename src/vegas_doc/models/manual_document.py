"""Typed input model for Manual Generator Word output."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path


@dataclass(frozen=True, slots=True)
class EquipmentSpec:
    """Manual equipment name, document code, and alarm product name."""

    name: str
    code: str
    product_name: str


EQUIPMENT_SPECS = (
    EquipmentSpec("Weighing Booth", "WB", "Blower"),
    EquipmentSpec("Clean Booth", "CB", "Fan"),
    EquipmentSpec("Sampling Booth", "SB", "Blower"),
    EquipmentSpec("ORABS", "OR", "Blower"),
)

IMAGE_LABELS = ("Main Screen", "Data Setting", "Alarm Screen", "Alarm Setting")


@dataclass(frozen=True, slots=True)
class InstrumentCounts:
    """Configured instrument quantities used to expand alarm rows."""

    temperature: int = 0
    humidity: int = 0
    differential_pressure: int = 0
    air_velocity: int = 0

    def named_counts(self) -> tuple[tuple[str, int], ...]:
        """Return immutable English alarm names and counts."""

        return (
            ("Temperature", self.temperature),
            ("Humidity", self.humidity),
            ("Differential Pressure", self.differential_pressure),
            ("Air Velocity", self.air_velocity),
        )


@dataclass(frozen=True, slots=True)
class ManualDocumentRequest:
    """Validated user request for one generated equipment manual."""

    template_path: Path
    output_directory: Path
    equipment: str
    document_suffix: str
    write_date: date
    image_paths: tuple[Path, ...]
    use_alarm_setting: bool
    use_instruments: bool
    instrument_counts: InstrumentCounts

    @property
    def equipment_spec(self) -> EquipmentSpec | None:
        """Return the selected supported equipment definition."""

        return next((item for item in EQUIPMENT_SPECS if item.name == self.equipment), None)

    @property
    def document_number(self) -> str:
        """Build the legacy-compatible GR-OM document number."""

        code = self.equipment_spec.code if self.equipment_spec is not None else ""
        return f"GR-OM-{code}{self.document_suffix.strip()}"

    @property
    def product_count(self) -> int:
        """Interpret the numeric suffix as the legacy product quantity."""

        suffix = self.document_suffix.strip()
        return int(suffix) if suffix.isdigit() else 0

    def output_filename(self, generated_at: datetime) -> str:
        """Return the timestamped filename used by Word Maker v9."""

        timestamp = generated_at.strftime("%Y%m%d_%H%M%S")
        return f"{_safe_filename(self.document_number)}_{_safe_filename(self.equipment)}_{timestamp}.docx"

    def validation_errors(self) -> tuple[str, ...]:
        """Return every actionable input error without touching output files."""

        errors: list[str] = []
        if self.equipment_spec is None:
            errors.append("장비명을 선택해 주세요.")
        suffix = self.document_suffix.strip()
        if not suffix:
            errors.append("문서번호 마지막 숫자/개수를 입력해 주세요.")
        elif not suffix.isdigit():
            errors.append("문서번호 칸에는 숫자만 입력해 주세요.")
        if self.template_path.suffix.lower() != ".docx" or not self.template_path.is_file():
            errors.append("유효한 Word DOCX 템플릿을 선택해 주세요.")
        if self.output_directory == Path() or not self.output_directory.is_dir():
            errors.append("유효한 Word 저장 폴더를 선택해 주세요.")

        required_count = 4 if self.use_alarm_setting else 3
        for index in range(required_count):
            path = self.image_paths[index] if index < len(self.image_paths) else Path()
            if not path.is_file():
                errors.append(f"{IMAGE_LABELS[index]} 이미지 파일을 선택해 주세요.")

        if self.use_instruments:
            for name, count in self.instrument_counts.named_counts():
                if count < 0:
                    errors.append(f"{name} 개수는 0 이상이어야 합니다.")
        return tuple(errors)


def _safe_filename(text: str) -> str:
    cleaned = re.sub(r'[\\/:*?"<>|]+', "_", text.strip())
    return cleaned or "output"
