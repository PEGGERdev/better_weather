from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Type, TypeVar


T = TypeVar("T")


@dataclass(frozen=True)
class MongoEntityBinding:
    collection: str
    prefix: str | None = None
    tags: tuple[str, ...] = ()


def mongo_entity(*, collection: str, prefix: str | None = None, tags: list[str] | tuple[str, ...] | None = None) -> Callable[[Type[T]], Type[T]]:
    resolved_tags = tuple(tags or [collection.replace("_", " ").title()])

    def decorator(cls: Type[T]) -> Type[T]:
        setattr(
            cls,
            "__mongo_entity__",
            MongoEntityBinding(
                collection=collection,
                prefix=prefix,
                tags=resolved_tags,
            ),
        )
        return cls

    return decorator


def get_mongo_entity_binding(value: object) -> MongoEntityBinding | None:
    binding = getattr(value, "__mongo_entity__", None)
    return binding if isinstance(binding, MongoEntityBinding) else None
