from typing import Optional
from app.repositories.base_repository import BaseRepository

class RecruiterRepository(BaseRepository):
    def __init__(self):
        super().__init__("recruiters")

    async def get_by_email(self, email: str) -> Optional[dict]:
        return await self.collection.find_one({"email": email})
