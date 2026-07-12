"""JSON configuration management without secret persistence."""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any


class ConfigManager:
    """Load and save non-secret JSON configuration values."""

    def __init__(self, config_path: Path) -> None:
        self._config_path = config_path
        self._values: dict[str, Any] = {}

    @property
    def config_path(self) -> Path:
        """Return the JSON configuration file path."""

        return self._config_path

    def load(self) -> dict[str, Any]:
        """Load configuration from disk, returning an empty mapping if absent."""

        if not self._config_path.exists():
            self._values = {}
            return dict(self._values)
        self._values = json.loads(self._config_path.read_text(encoding="utf-8"))
        return dict(self._values)

    def save(self, values: Mapping[str, Any]) -> None:
        """Persist non-secret values as formatted JSON."""

        self._config_path.parent.mkdir(parents=True, exist_ok=True)
        self._values = dict(values)
        self._config_path.write_text(
            json.dumps(self._values, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def get(self, key: str, default: Any = None) -> Any:
        """Return a loaded configuration value."""

        return self._values.get(key, default)
