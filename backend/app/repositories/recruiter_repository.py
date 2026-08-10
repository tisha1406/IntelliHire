from typing import Optional
from app.repositories.base_repository import BaseRepository

class RecruiterRepository(BaseRepository):
    def __init__(self):
        super().__init__("recruiters")

    async def get_by_email(self, email: str) -> Optional[dict]:
        return await self.collection.find_one({"email": email})

    async def get_by_company(self, company_id: str) -> list[dict]:
        from bson import ObjectId
        return await self.get_many({"company_id": str(company_id)}) # team.py uses current_user.sub (string) for company_id in recruiter doc

    async def get_active_by_id(self, recruiter_id: str) -> Optional[dict]:
        from bson import ObjectId
        return await self.collection.find_one({
            "_id": ObjectId(recruiter_id),
            "status": {"$ne": "suspended"},
            "is_deleted": {"$ne": True}
        })

    async def count_by_company(self, company_id: str) -> int:
        return await self.count({"company_id": str(company_id)})

