from datetime import UTC, datetime
from typing import Optional
from bson import ObjectId
from app.repositories.base_repository import BaseRepository


class ResumeRepository(BaseRepository):

    def __init__(self):
        super().__init__("resume_analyses")

    async def get_by_candidate(self, candidate_id: str) -> Optional[dict]:
        return await self.get_one({"candidate_id": ObjectId(candidate_id)})

    async def upsert(self, candidate_id: str, update_data: dict) -> bool:
        update_data["updated_at"] = datetime.now(UTC)
        result = await self.collection.update_one(
            {"candidate_id": ObjectId(candidate_id)},
            {"$set": update_data},
            upsert=True,
        )
        return result.acknowledged
