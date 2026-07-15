"""Shared display and Word-output date formats."""

from __future__ import annotations

import re
from datetime import date

DOCUMENT_DATE_FORMAT = "%Y.%m.%d"
QT_DOCUMENT_DATE_FORMAT = "yyyy.MM.dd"


def format_document_date(value: date) -> str:
    """Format a document date as YYYY.MM.DD."""

    return value.strftime(DOCUMENT_DATE_FORMAT)


def normalize_document_date(value: str) -> str:
    """Normalize a numeric date string to YYYY.MM.DD when possible."""

    match = re.fullmatch(r"\s*(\d{4})[-./](\d{1,2})[-./](\d{1,2})\s*", value)
    if match is None:
        return value
    year, month, day = (int(part) for part in match.groups())
    try:
        return format_document_date(date(year, month, day))
    except ValueError:
        return value
