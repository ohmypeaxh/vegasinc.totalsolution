"""Application composition root context."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

from vegas_doc.config.defaults import AppSettings
from vegas_doc.core.config_manager import ConfigManager
from vegas_doc.core.exception_handler import ExceptionHandler
from vegas_doc.core.logging_manager import LoggingManager
from vegas_doc.core.paths import user_data_dir
from vegas_doc.core.resource_manager import ResourceManager
from vegas_doc.core.service_container import ServiceContainer
from vegas_doc.core.theme_manager import ThemeManager


@dataclass(frozen=True, slots=True)
class ApplicationContext:
    """Container for application services and immutable bootstrap paths."""

    settings: AppSettings
    data_dir: Path
    services: ServiceContainer


def build_application_context(settings: AppSettings | None = None) -> ApplicationContext:
    """Build and register core services for production or tests."""

    app_settings = settings or AppSettings()
    data_dir = user_data_dir(app_settings.app_name)
    services = ServiceContainer()
    config = ConfigManager(data_dir / app_settings.config_filename)
    logger = LoggingManager(data_dir / app_settings.log_directory_name).configure()
    services.register_instance("config", config)
    services.register_instance("logger", logger)
    services.register_instance("resources", ResourceManager(Path(__file__).resolve().parents[1] / "resources"))
    services.register_instance("theme", ThemeManager())
    services.register_instance("exceptions", ExceptionHandler(logger))
    return ApplicationContext(app_settings, data_dir, services)
