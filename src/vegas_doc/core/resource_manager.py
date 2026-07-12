"""Resource path resolution for development and PyInstaller builds."""

from __future__ import annotations

import sys
from pathlib import Path


class ResourceManager:
    """Resolve packaged resources without depending on the current directory."""

    def __init__(self, resource_root: Path) -> None:
        self._resource_root = resource_root

    @classmethod
    def for_package(cls) -> "ResourceManager":
        """Create a resource manager for source or frozen PyInstaller execution."""

        frozen_root = getattr(sys, "_MEIPASS", None)
        if frozen_root:
            return cls(Path(frozen_root) / "vegas_doc" / "resources")
        return cls(Path(__file__).resolve().parents[1] / "resources")

    def path(self, *parts: str) -> Path:
        """Return an absolute path inside the resource root."""

        return self._resource_root.joinpath(*parts)

    def optional_path(self, *parts: str) -> Path | None:
        """Return a resource path only when it exists."""

        candidate = self.path(*parts)
        return candidate if candidate.exists() else None
