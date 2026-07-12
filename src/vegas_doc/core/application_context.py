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
    """Immutable bootstrap data plus a scoped service container."""

    settings: AppSettings
    data_dir: Path
    services: ServiceContainer


def build_application_context(settings: AppSettings | None = None, data_dir: Path | None = None) -> ApplicationContext:
    """Build and register core services for production or tests."""

    app_settings = settings or AppSettings()
    resolved_data_dir = data_dir or user_data_dir(app_settings.app_name)
    services = ServiceContainer()
    logger = LoggingManager(resolved_data_dir / app_settings.log_directory_name).configure()
    config = ConfigManager(resolved_data_dir / app_settings.config_filename, defaults={}, logger=logger)
    resources = ResourceManager.for_package()
    theme_path = resources.optional_path("themes", "default.qss")
    exceptions = ExceptionHandler(logger)
    services.register_instance(logging.Logger, logger)
    services.register_instance(ConfigManager, config)
    services.register_instance(ResourceManager, resources)
    services.register_instance(ThemeManager, ThemeManager(theme_path))
    services.register_instance(ExceptionHandler, exceptions)
    exceptions.install()
    return ApplicationContext(app_settings, resolved_data_dir, services)
