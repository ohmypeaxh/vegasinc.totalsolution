"""JSON configuration management without secret persistence."""

from __future__ import annotations

import json
import logging
from collections.abc import Mapping
from pathlib import Path
from typing import Any


class ConfigManager:
    """Load and save non-secret JSON configuration values."""

    def __init__(self, config_path: Path, defaults: Mapping[str, Any] | None = None, logger: logging.Logger | None = None) -> None:
        self._config_path = config_path
        self._defaults = dict(defaults or {})
        self._logger = logger
        self._values: dict[str, Any] = dict(self._defaults)

    @property
    def config_path(self) -> Path:
        """Return the JSON configuration file path."""

        return self._config_path

    def load(self) -> dict[str, Any]:
        """Load user configuration, safely falling back to defaults when invalid."""

        if not self._config_path.exists() or not self._config_path.read_text(encoding="utf-8").strip():
            self._values = dict(self._defaults)
            return dict(self._values)
        try:
            parsed = json.loads(self._config_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as error:
            if self._logger is not None:
                self._logger.warning("Ignoring malformed config file %s: %s", self._config_path, error)
            self._values = dict(self._defaults)
            return dict(self._values)
        if not isinstance(parsed, dict):
            if self._logger is not None:
                self._logger.warning("Ignoring non-object config file %s", self._config_path)
            self._values = dict(self._defaults)
            return dict(self._values)
        self._values = {**self._defaults, **parsed}
        return dict(self._values)

    def save(self, values: Mapping[str, Any]) -> None:
        """Persist non-secret values as formatted JSON."""

        self._config_path.parent.mkdir(parents=True, exist_ok=True)
        self._values = {**self._defaults, **dict(values)}
        self._config_path.write_text(
            json.dumps(self._values, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def get(self, key: str, default: Any = None) -> Any:
        """Return a loaded configuration value."""

        return self._values.get(key, default)
