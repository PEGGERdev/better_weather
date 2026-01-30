from bson import ObjectId
from pymongo import MongoClient, IndexModel
from pydantic import BaseModel
from typing import TypeVar, Type, Optional
import os

T = TypeVar('T', bound=BaseModel)

class MongoRepository:
    """Generic MongoDB repository for CRUD operations"""
    
    def __init__(self, collection_name: str, model_type: Type[T]):
        """Initialize repository with collection and model type"""
        mongo_url = os.getenv("MONGO_URL", "mongodb://localhost:27017")
        self.client = MongoClient(mongo_url)
        self.db = self.client["witterungsstation"]
        self.collection = self.db[collection_name]
        self.model_type = model_type

    def create(self, entity: T) -> str:
        """Insert new entity and return its ID"""
        result = self.collection.insert_one(entity.model_dump())
        return str(result.inserted_id)

    def read(self, entity_id: ObjectId) -> Optional[T]:
        """Find single entity by ID"""
        return self.collection.find_one({"_id": ObjectId(entity_id)})

    def read_all(self):
        """Retrieve all entities in collection"""
        return self.collection.find()

    def update(self, entity_id: ObjectId, entity: T):
        """Update existing entity"""
        return self.collection.update_one(
            {"_id": ObjectId(entity_id)},
            {"$set": entity.model_dump()}
        )

    def delete(self, entity_id: ObjectId):
        """Remove entity by ID"""
        return self.collection.delete_one({"_id": ObjectId(entity_id)})