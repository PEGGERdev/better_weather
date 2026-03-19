from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Generic, TypeVar

T = TypeVar("T")


@dataclass(frozen=True)
class RegistryItem(Generic[T]):
    id: str
    factory: T


class GenericRegistry(Generic[T]):
    def __init__(self, *, allow_replace: bool = False) -> None:
        self._allow_replace = bool(allow_replace)
        self._items: dict[str, T] = {}

    def register(self, id: str, factory: T) -> None:
        key = str(id)
        if (not self._allow_replace) and key in self._items:
            raise KeyError(f"Registry already contains id={key}")
        self._items[key] = factory

    def get(self, id: str) -> T:
        key = str(id)
        if key not in self._items:
            raise KeyError(f"Unknown registry id={key}")
        return self._items[key]

    def items(self) -> list[RegistryItem[T]]:
        return [RegistryItem(id=key, factory=value) for key, value in sorted(self._items.items())]

    def snapshot(self) -> dict[str, T]:
        return dict(self._items)

    def clear(self) -> None:
        self._items.clear()

    def validate(self, required_ids: list[str], *, label: str) -> None:
        for id in required_ids:
            key = str(id)
            if key not in self._items:
                raise KeyError(f"Missing {label} registration: {key}")


def register_many(registry: GenericRegistry[T], bindings: list[tuple[str, T]]) -> None:
    for id, factory in bindings:
        registry.register(id=id, factory=factory)
