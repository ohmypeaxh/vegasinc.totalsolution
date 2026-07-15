"""Recover numbered requirement rows from PDF and OCR text."""

from __future__ import annotations

import re
from dataclasses import dataclass

from vegas_doc.models.dq_document_data import section_key


@dataclass(frozen=True, slots=True)
class NumberedTextBlock:
    """One hierarchical number and its reconstructed multi-line text."""

    number: str
    text: str


_OCR_DIGIT_RUN = r"[0-9OoIl|ZzSsBbTt]+"
_HIERARCHICAL_NUMBER = rf"{_OCR_DIGIT_RUN}(?:\s*[.,:·]\s*{_OCR_DIGIT_RUN})*"
_NUMBER_ONLY = re.compile(rf"^\s*(?P<number>{_HIERARCHICAL_NUMBER})\s*(?:[.)])?\s*$")
_NUMBER_WITH_TEXT = re.compile(
    rf"^\s*(?P<number>{_HIERARCHICAL_NUMBER})\s*(?P<suffix>[.)]?)(?:\s+|\s*[|:\-]\s*)(?P<text>\S.*)$"
)
_PAGE_NOISE = re.compile(r"^(?:page|페이지)\s*\d+\s*/\s*\d+$", re.IGNORECASE)
_EXACT_NOISE = {
    "no",
    "no.",
    "yes",
    "비고",
    "요구사항",
    "공급자확인",
    "공급자 확인",
}


def numbered_text_blocks(text: str, start: str, end: str) -> tuple[NumberedTextBlock, ...]:
    """Return selected numbered rows, joining number-only OCR cells to following text."""

    start_key = section_key(start)
    end_key = section_key(end)
    blocks: list[NumberedTextBlock] = []
    current_number: str | None = None
    current_text: list[str] = []

    def in_range(number: str) -> bool:
        key = section_key(number)
        return key >= start_key and (key <= end_key or key[: len(end_key)] == end_key)

    def flush() -> None:
        nonlocal current_number, current_text
        if current_number is not None:
            content = re.sub(r"\s+", " ", " ".join(current_text)).strip()
            if content:
                blocks.append(NumberedTextBlock(current_number, content))
        current_number = None
        current_text = []

    for raw_line in text.splitlines():
        line = raw_line.strip(" \t•*|□☑☒✓✔")
        if not line or _is_noise(line):
            continue
        parsed = _parse_numbered_line(line)
        if parsed is not None:
            number, content, range_boundary = parsed
            number = _restore_missing_separator(number, start_key, end_key)
            if in_range(number):
                flush()
                current_number = number
                if content:
                    current_text.append(content)
                continue
            if range_boundary:
                flush()
                continue
        if current_number is not None:
            current_text.append(line)

    flush()
    return tuple(blocks)


def _parse_numbered_line(line: str) -> tuple[str, str, bool] | None:
    only = _NUMBER_ONLY.fullmatch(line)
    if only is not None:
        return _normalize_number(only.group("number")), "", True
    with_text = _NUMBER_WITH_TEXT.fullmatch(line)
    if with_text is None:
        return None
    number = _normalize_number(with_text.group("number"))
    suffix = with_text.group("suffix")
    range_boundary = "." in number or suffix == "."
    return number, with_text.group("text").strip(), range_boundary


def _normalize_number(value: str) -> str:
    translation = str.maketrans(
        {
            "O": "0",
            "o": "0",
            "I": "1",
            "l": "1",
            "|": "1",
            "Z": "2",
            "z": "2",
            "S": "5",
            "s": "5",
            "B": "8",
            "b": "8",
            "T": "7",
            "t": "7",
            ",": ".",
            ":": ".",
            "·": ".",
        }
    )
    return re.sub(r"\s+", "", value).translate(translation)


def _restore_missing_separator(number: str, start_key: tuple[int, ...], end_key: tuple[int, ...]) -> str:
    """Recover section numbers such as ``731`` when OCR drops the dot in ``7.31``."""

    if "." in number or not number.isdigit() or len(start_key) != 1 or len(end_key) != 1:
        return number
    for root in range(start_key[0], end_key[0] + 1):
        prefix = str(root)
        if number.startswith(prefix) and len(number) > len(prefix):
            return f"{prefix}.{number[len(prefix):]}"
    return number


def _is_noise(line: str) -> bool:
    compact = re.sub(r"\s+", " ", line).strip()
    if compact.casefold() in _EXACT_NOISE:
        return True
    if _PAGE_NOISE.fullmatch(compact):
        return True
    return compact.upper().startswith("DP-")
