"""Core foundation tests that do not require native Qt libraries."""

from __future__ import annotations

from vegas_doc.core.config_manager import ConfigManager
from vegas_doc.core.logging_manager import LoggingManager


def test_config_manager_round_trip(tmp_path) -> None:
    """Non-secret JSON configuration can be saved and loaded."""

    manager = ConfigManager(tmp_path / "settings.json")
    manager.save({"theme": "light"})

    assert manager.load() == {"theme": "light"}


def test_logging_manager_creates_daily_log_file(tmp_path) -> None:
    """Logging manager writes under the configured log directory."""

    logger = LoggingManager(tmp_path / "logs", "vegas_doc_test_core").configure()
    logger.info("startup")

    assert list((tmp_path / "logs").glob("*.log"))
