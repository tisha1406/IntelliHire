from typing import Optional

from bson import ObjectId

from app.db.mongo import get_database


class BaseRepository:
    """
    Generic MongoDB repository providing common CRUD operations.
    """

    def __init__(self, collection_name: str):
        self.collection_name = collection_name

    @property
    def collection(self):
        """
        Lazily fetch the MongoDB collection.

        This ensures the database connection has already been
        established during FastAPI startup.
        """
        db = get_database()
        return db[self.collection_name]

    async def create(self, document: dict) -> str:
        result = await self.collection.insert_one(document)
        return str(result.inserted_id)

    async def get_by_id(self, document_id: str) -> Optional[dict]:
        return await self.collection.find_one(
            {"_id": ObjectId(document_id)}
        )

    async def get_one(self, query: dict) -> Optional[dict]:
        return await self.collection.find_one(query)

    async def get_many(
        self,
        query: dict = {},
        limit: int = 100,
        skip: int = 0,
    ) -> list[dict]:

        cursor = (
            self.collection
            .find(query)
            .skip(skip)
            .limit(limit)
        )

        return await cursor.to_list(length=limit)

    async def update(
        self,
        document_id: str,
        update_data: dict,
    ) -> bool:

        result = await self.collection.update_one(
            {"_id": ObjectId(document_id)},
            {"$set": update_data},
        )

        return result.modified_count > 0

    async def delete(self, document_id: str) -> bool:

        result = await self.collection.delete_one(
            {"_id": ObjectId(document_id)}
        )

        return result.deleted_count > 0

    async def count(self, query: dict = {}) -> int:
        return await self.collection.count_documents(query)