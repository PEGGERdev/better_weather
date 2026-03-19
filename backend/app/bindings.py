from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Type
import inspect
import sys

from fastapi import APIRouter
from pydantic import BaseModel

try:
    from data import models as data_models
    from data.mongo_repository import MongoRepository
    from routing.router import router_create
except ModuleNotFoundError as exc:
    if exc.name not in {"data", "routing"}:
        raise
    from backend.data import models as data_models
    from backend.data.mongo_repository import MongoRepository
    from backend.routing.router import router_create

try:
    from shared.mongo_entity import get_mongo_entity_binding
except ModuleNotFoundError:
    sys.path.append(str(Path(__file__).resolve().parents[2]))
    from shared.mongo_entity import get_mongo_entity_binding


@dataclass(frozen=True)
class EntityDefinition:
    model: Type[BaseModel]
    collection: str
    prefix: str
    tags: list[str]


def _build_entity_definitions() -> list[EntityDefinition]:
    definitions: list[EntityDefinition] = []

    for _, candidate in inspect.getmembers(data_models, inspect.isclass):
        if not issubclass(candidate, BaseModel) or candidate is BaseModel:
            continue

        binding = get_mongo_entity_binding(candidate)
        if binding is None:
            continue

        definitions.append(
            EntityDefinition(
                model=candidate,
                collection=binding.collection,
                prefix=binding.prefix or f"/{binding.collection}",
                tags=list(binding.tags),
            )
        )

    return definitions


ENTITY_DEFINITIONS = _build_entity_definitions()


def build_entity_routers() -> list[APIRouter]:
    routers: list[APIRouter] = []

    for entity in ENTITY_DEFINITIONS:
        repository = MongoRepository(
            collection_name=entity.collection,
            model_type=entity.model,
        )
        router = router_create(
            model=entity.model,
            repository=repository,
            prefix=entity.prefix,
            tags=entity.tags,
        )
        routers.append(router)

    return routers
