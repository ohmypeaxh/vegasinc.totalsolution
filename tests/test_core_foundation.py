"""Core foundation tests that do not require native Qt libraries."""

from __future__ import annotations

import logging

from vegas_doc.core.config_manager import ConfigManager
from vegas_doc.core.logging_manager import LoggingManager
from vegas_doc.core.service_container import ServiceContainer


def test_config_manager_round_trip(tmp_path) -> None:
    """Non-secret JSON configuration can be saved and loaded."""

    manager = ConfigManager(tmp_path / "settings.json", defaults={"theme": "light"})
    manager.save({"window": "maximized"})

    assert manager.load() == {"theme": "light", "window": "maximized"}


def test_config_manager_handles_malformed_json(tmp_path) -> None:
    """Malformed user configuration safely falls back to defaults."""

    config_path = tmp_path / "settings.json"
    config_path.write_text("{bad json", encoding="utf-8")
    manager = ConfigManager(config_path, defaults={"theme": "light"})

    assert manager.load() == {"theme": "light"}


def test_logging_manager_creates_daily_log_file(tmp_path) -> None:
    """Logging manager writes under the configured log directory."""

    logger = LoggingManager(tmp_path / "logs", "vegas_doc_test_core_create").configure()
    logger.info("startup")

    assert list((tmp_path / "logs").glob("*.log"))


def test_logging_manager_is_idempotent(tmp_path) -> None:
    """Repeated logging initialization does not add duplicate handlers."""

    logger_name = "vegas_doc_test_core_idempotent"
    first = LoggingManager(tmp_path / "logs", logger_name).configure()
    second = LoggingManager(tmp_path / "logs", logger_name).configure()

    assert first is second
    assert len([handler for handler in second.handlers if isinstance(handler, logging.Handler)]) == 1


def test_service_container_registers_and_resolves_by_abstraction() -> None:
    """Services are registered and resolved by their abstraction type."""

    class ExampleService:
        pass

    service = ExampleService()
    container = ServiceContainer()
    container.register_instance(ExampleService, service)

    assert container.resolve(ExampleService) is service
