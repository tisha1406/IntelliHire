from typing import List
from bson import ObjectId
from app.repositories.base_repository import BaseRepository


class ActivityLogRepository(BaseRepository):

    def __init__(self):
        super().__init__("activity_log")

    async def get_by_candidate(self, candidate_id: str, limit: int = 50) -> List[dict]:
        return await self.collection.find(
            {"candidate_id": ObjectId(candidate_id)}
        ).sort("created_at", -1).limit(limit).to_list(length=limit)
