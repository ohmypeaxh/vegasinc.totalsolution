"""Default non-secret application configuration values."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class AppSettings:
    """Typed, non-secret settings required to bootstrap the application."""

    app_name: str = "Vegas Total Solution Doc"
    organization_name: str = "Vegas Inc."
    config_filename: str = "settings.json"
    log_directory_name: str = "logs"
    plugins_package: str = "vegas_doc.builtin_plugins"
    external_plugins_directory: Path | None = None
