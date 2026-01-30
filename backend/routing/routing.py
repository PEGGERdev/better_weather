
from __future__ import annotations
from dataclasses import dataclass
from functools import wraps
from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from routing.router import router_create
from typing import Callable, Type, TypeVar, Any

from routing.router import router_create
from data.mongo_repository import MongoRepository
from data.dto import *

# Generic type for Pydantic models
T = TypeVar('T', bound=BaseModel)

@dataclass(frozen=True)
class EntityBinding:
    model: Type[T]
    collection: str
    prefix: str
    tags: list[str]
    router: APIRouter

_REGISTRY: list[EntityBinding] = []

def get_routers() -> list[APIRouter]:
    return [b.router for b in _REGISTRY]

def mongo_entity(
    *,
    collection: str,
    prefix: str | None = None,
    tags: list[str] | None = None,
) -> Callable[[Type[T]], Type[T]]:
    """
    Class decorator:
    - reads config (collection/prefix/tags)
    - builds MongoRepository + APIRouter
    - registers Router globally
    """
    def decorator(model_cls: Type[T]) -> Type[T]:
        effective_prefix = prefix or f"/{collection}"
        effective_tags = tags or [collection]


        repo = MongoRepository(collection_name=collection, model_type=model_cls)
        router = router_create(
            model=model_cls,
            repository=repo,
            prefix=effective_prefix,
            tags=effective_tags,
        )

        _REGISTRY.append(
            EntityBinding(
                model=model_cls,
                collection=collection,
                prefix=effective_prefix,
                tags=effective_tags,
                router=router,
            )
        )
        return model_cls

    return decorator

class Routing():
    def __init__(self):
        self.app = FastAPI()
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_methods=["*"],
            allow_headers=["*"],
        )
        for router in get_routers():
            self.app.include_router(router)
        
    def get_app(self):
        return self.app
