"""Resource path resolution."""

from __future__ import annotations

from pathlib import Path


class ResourceManager:
    """Resolve packaged and project-level resources."""

    def __init__(self, resource_root: Path) -> None:
        self._resource_root = resource_root

    def path(self, *parts: str) -> Path:
        """Return an absolute path inside the resource root."""

        return self._resource_root.joinpath(*parts)
