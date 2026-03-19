from __future__ import annotations

from typing import Any, Callable

from core.registry import GenericRegistry

ServiceFactory = Callable[[Any], Any]
ControllerFactory = Callable[[Any], Any]

_SERVICE_REGISTRY = GenericRegistry[ServiceFactory]()
_CONTROLLER_REGISTRY = GenericRegistry[ControllerFactory]()


def register_service_factory(name: str, factory: ServiceFactory) -> None:
    _SERVICE_REGISTRY.register(str(name), factory)


def register_controller_factory(name: str, factory: ControllerFactory) -> None:
    _CONTROLLER_REGISTRY.register(str(name), factory)


def get_service_factories() -> dict[str, ServiceFactory]:
    return _SERVICE_REGISTRY.snapshot()


def get_controller_factories() -> dict[str, ControllerFactory]:
    return _CONTROLLER_REGISTRY.snapshot()


def validate_runtime_registry(*, required_services: list[str], required_controllers: list[str]) -> None:
    _SERVICE_REGISTRY.validate(required_services, label="service")
    _CONTROLLER_REGISTRY.validate(required_controllers, label="controller")


def reset_runtime_registry() -> None:
    _SERVICE_REGISTRY.clear()
    _CONTROLLER_REGISTRY.clear()
