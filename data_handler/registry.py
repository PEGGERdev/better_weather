from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Type, TypeVar

T = TypeVar("T")


@dataclass(frozen=True)
class ServiceBinding:
    kind: str
    name: str
    service_cls: type


_REGISTRY: dict[str, dict[str, type]] = {}


def register_service(*, kind: str, name: str) -> Callable[[Type[T]], Type[T]]:
    def decorator(service_cls: Type[T]) -> Type[T]:
        bucket = _REGISTRY.setdefault(kind, {})
        bucket[name] = service_cls
        return service_cls

    return decorator


def get_service(kind: str, name: str) -> type:
    bucket = _REGISTRY.get(kind, {})
    service_cls = bucket.get(name)
    if service_cls is None:
        raise KeyError(f"Unknown service: {kind}:{name}")
    return service_cls


def get_services(kind: str) -> list[ServiceBinding]:
    bucket = _REGISTRY.get(kind, {})
    return [
        ServiceBinding(kind=kind, name=name, service_cls=service_cls)
        for name, service_cls in sorted(bucket.items(), key=lambda item: item[0])
    ]
