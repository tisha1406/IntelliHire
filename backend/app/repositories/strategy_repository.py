from app.repositories.base_repository import BaseRepository
from datetime import datetime, timezone
from bson import ObjectId

class StrategyRepository(BaseRepository):

    def __init__(self):
        super().__init__("strategies")

    async def get_by_strategy_id_and_version(self, strategy_id: str, version: int):
        return await self.get_one(
            {"strategy_id": strategy_id, "version": version}
        )
        
    async def get_latest_version(self, strategy_id: str):
        # Sort by version descending and get the first one
        cursor = self.collection.find({"strategy_id": strategy_id}).sort("version", -1).limit(1)
        documents = await cursor.to_list(length=1)
        if documents:
            return documents[0]
        return None

    async def get_all_unique_strategies(self, limit: int = 10, skip: int = 0):
        # We can either return the latest version for each strategy, or all versions. 
        # For an admin list view, returning the latest version of each unique strategy is usually best.
        pipeline = [
            {"$sort": {"version": -1}},
            {"$group": {
                "_id": "$strategy_id",
                "latest_document": {"$first": "$$ROOT"}
            }},
            {"$replaceRoot": {"newRoot": "$latest_document"}},
            {"$sort": {"created_at": -1}},
            {"$skip": skip},
            {"$limit": limit}
        ]
        cursor = self.collection.aggregate(pipeline)
        return await cursor.to_list(length=limit)
        
    async def count_unique_strategies(self):
        pipeline = [
            {"$group": {"_id": "$strategy_id"}}
        ]
        cursor = self.collection.aggregate(pipeline)
        docs = await cursor.to_list(length=None)
        return len(docs)

    async def get_all_versions(self, strategy_id: str):
        cursor = self.collection.find({"strategy_id": strategy_id}).sort("version", -1)
        return await cursor.to_list(length=None)