"""Application logging configuration."""

from __future__ import annotations

import logging
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path


class LoggingManager:
    """Configure application logging with daily rotating files."""

    def __init__(self, log_directory: Path, logger_name: str = "vegas_doc") -> None:
        self._log_directory = log_directory
        self._logger_name = logger_name

    def configure(self) -> logging.Logger:
        """Create a logger writing under logs/yyyy-mm-dd.log."""

        self._log_directory.mkdir(parents=True, exist_ok=True)
        logger = logging.getLogger(self._logger_name)
        logger.setLevel(logging.INFO)
        logger.propagate = False
        if not logger.handlers:
            log_path = self._log_directory / f"{datetime.now():%Y-%m-%d}.log"
            handler = RotatingFileHandler(log_path, maxBytes=2_000_000, backupCount=10, encoding="utf-8")
            handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s - %(message)s"))
            logger.addHandler(handler)
        return logger
