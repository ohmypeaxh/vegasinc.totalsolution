"""Small dependency injection container."""

from __future__ import annotations

from collections.abc import Callable
from typing import TypeVar

T = TypeVar("T")


class ServiceContainer:
    """Register and resolve application services by string keys."""

    def __init__(self) -> None:
        self._factories: dict[str, Callable[[ServiceContainer], object]] = {}
        self._instances: dict[str, object] = {}

    def register_instance(self, key: str, instance: object) -> None:
        """Register an already constructed service."""

        self._instances[key] = instance

    def register_factory(self, key: str, factory: Callable[[ServiceContainer], object]) -> None:
        """Register a lazy service factory."""

        self._factories[key] = factory

    def resolve(self, key: str, expected_type: type[T] | None = None) -> T | object:
        """Resolve a service by key and optionally enforce its type."""

        if key not in self._instances:
            if key not in self._factories:
                raise KeyError(f"Service is not registered: {key}")
            self._instances[key] = self._factories[key](self)
        instance = self._instances[key]
        if expected_type is not None and not isinstance(instance, expected_type):
            raise TypeError(f"Service {key} is not {expected_type.__name__}")
        return instance
