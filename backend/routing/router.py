from __future__ import annotations

from enum import Enum
from datetime import datetime
from typing import Any, Callable, Dict, Sequence, Type, TypeVar, cast

from bson import ObjectId
from fastapi import APIRouter, Body, HTTPException, Query, Response, status
from pydantic import BaseModel, ValidationError

try:
    from routing.error_mapper import map_http_errors
    from routing.object_id import parse_object_id
except ModuleNotFoundError as exc:
    if exc.name != "routing":
        raise
    from backend.routing.error_mapper import map_http_errors
    from backend.routing.object_id import parse_object_id

T = TypeVar("T", bound=BaseModel)


def _to_api_json(value: Any) -> Any:
    if isinstance(value, ObjectId):
        return str(value)

    if isinstance(value, datetime):
        return value.isoformat()

    if isinstance(value, list):
        return [_to_api_json(item) for item in value]

    if isinstance(value, tuple):
        return [_to_api_json(item) for item in value]

    if isinstance(value, dict):
        return {str(key): _to_api_json(item) for key, item in value.items()}

    return value


class GenericCrudRouter:
    """Generic CRUD router builder with model validation and ObjectId handling."""

    def __init__(
        self,
        model: Type[T],
        repository,
        prefix: str,
        tags: Sequence[str | Enum] | None = None,
    ) -> None:
        self.model = model
        self.repository = repository
        self.prefix = prefix
        self.tags = cast(list[str | Enum], tags or [prefix.strip("/")])

    def with_object_id_validation(self, func: Callable) -> Callable:
        from functools import wraps

        @wraps(func)
        async def wrapper(entity_id: str, *args, **kwargs):
            validated = parse_object_id(entity_id)
            return await func(validated, *args, **kwargs)

        return wrapper

    def build(self) -> APIRouter:
        model = self.model
        repository = self.repository

        router = APIRouter(prefix=self.prefix, tags=self.tags)

        @router.post("/")
        @map_http_errors
        async def create(entity_data: Dict[str, Any] = Body(...)):
            try:
                entity = model.model_validate(entity_data)
            except ValidationError as e:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=e.errors(),
                ) from e

            entity_id = repository.create(entity)
            return {"id": str(entity_id)}

        @router.get("/")
        @map_http_errors
        async def read_all(limit: int = Query(default=500, ge=1, le=10000)):
            entities = repository.read_all(limit=limit)
            return _to_api_json(entities)

        @router.get("/{entity_id}")
        @map_http_errors
        @self.with_object_id_validation
        async def read(entity_id: str):
            entity = repository.read(entity_id)
            if not entity:
                raise HTTPException(status.HTTP_404_NOT_FOUND)
            return _to_api_json(entity)

        @router.put("/{entity_id}")
        @map_http_errors
        @self.with_object_id_validation
        async def update(entity_id: str, entity_data: Dict[str, Any] = Body(...)):
            try:
                entity = model.model_validate(entity_data)
            except ValidationError as e:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=e.errors(),
                ) from e

            result = repository.update(entity_id, entity)
            if result.matched_count == 0:
                raise HTTPException(status.HTTP_404_NOT_FOUND, "Entity not found")
            return {
                "matched_count": result.matched_count,
                "modified_count": result.modified_count,
            }

        @router.delete("/{entity_id}")
        @map_http_errors
        @self.with_object_id_validation
        async def delete(entity_id: str):
            result = repository.delete(entity_id)
            if result.deleted_count == 0:
                raise HTTPException(status.HTTP_404_NOT_FOUND, "Entity not found")
            return Response(status_code=status.HTTP_204_NO_CONTENT)

        return router


def router_create(
    model: Type[T],
    repository,
    prefix: str,
    tags: Sequence[str | Enum] | None = None,
) -> APIRouter:
    return GenericCrudRouter(
        model=model,
        repository=repository,
        prefix=prefix,
        tags=tags,
    ).build()
