from typing import List
from bson import ObjectId
from app.repositories.base_repository import BaseRepository


class SupportRepository(BaseRepository):

    def __init__(self):
        super().__init__("support_tickets")

    async def get_by_candidate(self, candidate_id: str) -> List[dict]:
        return await self.collection.find(
            {"candidate_id": ObjectId(candidate_id)}
        ).sort("created_at", -1).to_list(length=None)
