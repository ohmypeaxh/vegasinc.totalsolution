"""Small dependency injection container keyed by service abstractions."""

from __future__ import annotations

from collections.abc import Callable
from typing import TypeVar, cast

T = TypeVar("T")
ServiceFactory = Callable[["ServiceContainer"], object]


class ServiceContainer:
    """Register and resolve application services by abstraction type."""

    def __init__(self) -> None:
        self._factories: dict[type[object], ServiceFactory] = {}
        self._instances: dict[type[object], object] = {}

    def register_instance(self, abstraction: type[T], instance: T) -> None:
        """Register an already constructed service for an abstraction."""

        self._instances[cast(type[object], abstraction)] = instance

    def register_factory(self, abstraction: type[T], factory: Callable[["ServiceContainer"], T]) -> None:
        """Register a lazy service factory for an abstraction."""

        self._factories[cast(type[object], abstraction)] = factory

    def resolve(self, abstraction: type[T]) -> T:
        """Resolve a service by abstraction type."""

        key = cast(type[object], abstraction)
        if key not in self._instances:
            if key not in self._factories:
                raise KeyError(f"Service is not registered: {abstraction.__name__}")
            self._instances[key] = self._factories[key](self)
        instance = self._instances[key]
        if not isinstance(instance, abstraction):
            raise TypeError(f"Service {abstraction.__name__} resolved to {type(instance).__name__}")
        return instance
