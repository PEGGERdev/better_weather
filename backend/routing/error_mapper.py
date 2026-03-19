from __future__ import annotations

from functools import wraps
from typing import Any, Awaitable, Callable, TypeVar

from fastapi import HTTPException


F = TypeVar("F", bound=Callable[..., Awaitable[Any]])


def map_http_errors(func: F) -> F:
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(
                status_code=getattr(exc, "status_code", 500),
                detail={
                    "error": str(exc),
                    "type": exc.__class__.__name__,
                },
            ) from exc

    return wrapper  # type: ignore[return-value]
