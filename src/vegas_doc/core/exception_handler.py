"""Central exception logging and reporting helper."""

from __future__ import annotations

import logging
import sys
from collections.abc import Callable
from types import TracebackType

UserReporter = Callable[[str, str], None]


class ExceptionHandler:
    """Log unexpected errors and optionally report sanitized messages to users."""

    def __init__(self, logger: logging.Logger, reporter: UserReporter | None = None) -> None:
        self._logger = logger
        self._reporter = reporter

    def handle(self, error: BaseException, context: str = "Unhandled exception") -> None:
        """Record an exception and notify through the configured reporter."""

        self._logger.exception("%s: %s", context, error)
        if self._reporter is not None:
            self._reporter("Unexpected error", f"{context}. See application logs for details.")

    def excepthook(self, exc_type: type[BaseException], exc: BaseException, tb: TracebackType | None) -> None:
        """Handle Python-level unhandled exceptions."""

        self._logger.error("Unhandled exception", exc_info=(exc_type, exc, tb))
        if self._reporter is not None:
            self._reporter("Unexpected error", "An unexpected error occurred. See application logs for details.")

    def install(self) -> None:
        """Install this handler as the process-level Python exception hook."""

        sys.excepthook = self.excepthook

    def wrap_slot(self, slot):  # type: ignore[no-untyped-def]
        """Wrap practical Qt slots so exceptions are logged rather than swallowed by Qt."""

        def wrapped(*args, **kwargs):  # type: ignore[no-untyped-def]
            try:
                return slot(*args, **kwargs)
            except Exception as error:  # noqa: BLE001 - intentional boundary logging
                self.handle(error, f"Qt slot failed: {getattr(slot, '__name__', repr(slot))}")
                return None

        return wrapped
