"""Path helpers for Windows-compatible application storage."""

from __future__ import annotations

import os
from pathlib import Path


def user_data_dir(app_name: str) -> Path:
    """Return the per-user writable data directory for the application."""

    base = Path(os.getenv("APPDATA") or Path.home())
    return base / app_name.replace(" ", "")
