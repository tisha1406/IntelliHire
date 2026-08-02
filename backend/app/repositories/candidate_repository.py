from bson import ObjectId

from app.repositories.base_repository import BaseRepository


class CandidateRepository(BaseRepository):

    def __init__(self):
        super().__init__("candidates")

    # ==========================================
    # Generic CRUD Operations
    # ==========================================

    async def list(self, filters=None):
        return await self.get_many(filters or {})

    async def get(self, candidate_id):
        return await self.get_by_id(candidate_id)

    async def create(self, data):
        return await super().create(data)

    async def update(self, candidate_id, data):
        return await super().update(candidate_id, data)

    async def delete(self, candidate_id):
        return await super().delete(candidate_id)

    # ==========================================
    # Candidate Specific Queries
    # ==========================================

    async def get_by_campaign(self, campaign_id: str):
        return await self.get_many(
            {"campaign_id": campaign_id}
        )

    async def get_by_email(self, email: str):
        return await self.get_one(
            {"email": email}
        )

    async def get_by_user_id(self, user_id: str):
        return await self.get_one(
            {"user_id": ObjectId(user_id)}
        )