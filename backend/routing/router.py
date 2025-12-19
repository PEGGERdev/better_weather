from functools import wraps
from fastapi import APIRouter, HTTPException, status, Response, Body
from bson import ObjectId, json_util
from typing import Type, TypeVar, Callable
from pydantic import BaseModel
import json
import traceback

# Generic type for Pydantic models
T = TypeVar('T', bound=BaseModel)

def router_create(
    model: Type[T],
    repository,
    prefix: str,
    tags: list[str] = None
) -> APIRouter:
    """
    Factory function to create CRUD routes for a given model
    Args:
        model: Pydantic model class
        repository: Database repository instance
        prefix: URL path prefix for routes
        tags: OpenAPI tags for documentation
    Returns:
        APIRouter: Configured router with CRUD endpoints
    """
    router = APIRouter(prefix=prefix, tags=tags or [prefix.strip('/')])

    def _validate_object_id(entity_id: str) -> ObjectId:
        """
        Validates and converts string to ObjectId
        Args:
            entity_id: ID as string
        Returns:
            ObjectId: Valid MongoDB ID
        Raises:
            HTTPException: 400 if invalid format
        """
        if not ObjectId.is_valid(entity_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid ID format"
            )
        return ObjectId(entity_id)

    # Decorators
    def handle_exceptions(func: Callable) -> Callable:
        """
        Global exception handler decorator
        Converts exceptions to HTTP responses
        """
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(
                    status_code=getattr(e, 'status_code', 500),
                    detail={
                        "error": str(e),
                        "type": e.__class__.__name__,
                        "traceback": traceback.format_exc().splitlines()
                    }
                )
        return wrapper

    def with_object_id_validation(func: Callable) -> Callable:
        """
        Decorator to validate ObjectID parameters
        Converts string ID to ObjectId before passing to route
        """
        @wraps(func)
        async def wrapper(entity_id: str, *args, **kwargs):
            entity_id = _validate_object_id(entity_id)
            return await func(entity_id, *args, **kwargs)
        return wrapper


    # CRUD Endpoints
    @router.post("/")
    @handle_exceptions
    async def create(entity: model = Body(...)):
        """
        Creates a new entity
        Args:
            entity: Data to create (validated by model)
        Returns:
            dict: Contains the generated ID
        """
        entity_id = repository.create(entity)
        return {"id": str(entity_id)}

    @router.get("/")
    @handle_exceptions
    async def read_all():
        """
        Retrieves all entities
        Returns:
            list: All found entities
        """
        entities = repository.read_all()
        return json.loads(json_util.dumps(entities))

    @router.get("/{entity_id}")
    @handle_exceptions
    @with_object_id_validation
    async def read(entity_id: str):
        """
        Retrieves a specific entity by ID
        Args:
            entity_id: Validated MongoDB ObjectID
        Returns:
            dict: The found entity
        Raises:
            HTTPException: 404 if not found
        """
        entity = repository.read(entity_id)
        if not entity:
            raise HTTPException(status.HTTP_404_NOT_FOUND)
        return json.loads(json_util.dumps(entity))

    @router.put("/{entity_id}")
    @handle_exceptions
    @with_object_id_validation
    async def update(entity_id: str, entity: model = Body(...)):
        """
        Updates an existing entity
        Args:
            entity_id: MongoDB ObjectID
            entity: New data (validated by model)
        Returns:
            dict: Number of modified documents
        Raises:
            HTTPException: 404 if no document was modified
        """
        result = repository.update(entity_id, entity)
        if not result.modified_count:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Entity not found")
        return {"modified_count": result.modified_count}

    @router.delete("/{entity_id}")
    @handle_exceptions
    @with_object_id_validation
    async def delete(entity_id: str):
        """
        Deletes an entity by ID
        Args:
            entity_id: MongoDB ObjectID
        Returns:
            Response: 204 No Content on success
        Raises:
            HTTPException: 404 if no document was deleted
        """
        result = repository.delete(entity_id)
        if result.deleted_count == 0:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Entity not found")
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    return router