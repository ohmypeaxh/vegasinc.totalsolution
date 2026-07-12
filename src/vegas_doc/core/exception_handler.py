"""Central exception logging helper."""

from __future__ import annotations

import logging


class ExceptionHandler:
    """Log unexpected errors in a single location."""

    def __init__(self, logger: logging.Logger) -> None:
        self._logger = logger

    def handle(self, error: BaseException, context: str = "Unhandled exception") -> None:
        """Record an exception with context."""

        self._logger.exception("%s: %s", context, error)
