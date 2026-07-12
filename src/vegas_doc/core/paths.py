"""Path helpers for Windows-compatible application storage."""

from __future__ import annotations

from pathlib import Path

from platformdirs import user_data_dir as platform_user_data_dir


def user_data_dir(app_name: str) -> Path:
    """Return the per-user writable data directory for the application."""

    return Path(platform_user_data_dir(app_name, appauthor="Vegas Inc."))
