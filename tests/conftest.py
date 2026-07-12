"""Shared test helpers."""

from __future__ import annotations

import pytest


def require_qt() -> None:
    """Skip Qt tests when native GUI libraries are unavailable."""

    try:
        from PySide6.QtWidgets import QApplication  # noqa: F401
    except ImportError as exc:
        pytest.skip(f"PySide6 native dependency unavailable: {exc}")
