from datetime import UTC, datetime
from typing import Optional
from app.repositories.base_repository import BaseRepository


class InvitationRepository(BaseRepository):

    def __init__(self):
        super().__init__("candidate_invitations")

    async def get_by_token(self, token: str) -> Optional[dict]:
        return await self.get_one({"token": token, "used": False})
    
    async def mark_used(self, token: str) -> bool:
        result = await self.collection.update_one(
            {"token": token},
            {"$set": {"used": True, "used_at": datetime.now(UTC)}}
        )
        return result.modified_count > 0
