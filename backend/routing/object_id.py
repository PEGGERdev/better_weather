from __future__ import annotations

from bson import ObjectId
from fastapi import HTTPException, status


def parse_object_id(entity_id: str) -> ObjectId:
    if not ObjectId.is_valid(entity_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid ID format",
        )
    return ObjectId(entity_id)
