"""Build and version metadata exposed without secrets."""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True, slots=True)
class BuildInfo:
    product: str = "Vegas Total Solution Doc"
    version: str = "0.1.0"
    build_number: str = os.getenv("VEGAS_BUILD_NUMBER", "development")
    build_date: str = os.getenv("VEGAS_BUILD_DATE", date.today().isoformat())
    commit: str = os.getenv("VEGAS_GIT_COMMIT", "development")


BUILD_INFO = BuildInfo()
