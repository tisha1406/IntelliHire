from typing import List
from bson import ObjectId
from app.repositories.base_repository import BaseRepository


class NotificationRepository(BaseRepository):

    def __init__(self):
        super().__init__("candidate_notifications")

    async def get_unread_count(self, candidate_id: str) -> int:
        return await self.count({
            "candidate_id": ObjectId(candidate_id),
            "read": False
        })

    async def get_by_candidate(self, candidate_id: str, limit: int = 50) -> List[dict]:
        return await self.collection.find(
            {"candidate_id": ObjectId(candidate_id)}
        ).sort("created_at", -1).limit(limit).to_list(length=limit)

    async def mark_read(self, candidate_id: str, notification_ids: List[str] = None) -> bool:
        query = {"candidate_id": ObjectId(candidate_id)}
        if notification_ids:
            query["_id"] = {"$in": [ObjectId(nid) for nid in notification_ids]}
        
        result = await self.collection.update_many(
            query,
            {"$set": {"read": True}}
        )
        return result.modified_count > 0
