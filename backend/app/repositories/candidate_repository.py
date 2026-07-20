from app.repositories.base_repository import BaseRepository


class CandidateRepository(BaseRepository):

    def __init__(self):
        super().__init__("candidates")

    async def get_by_campaign(self, campaign_id: str):
        return await self.get_many(
            {"campaign_id": campaign_id}
        )

    async def get_by_email(self, email: str):
        return await self.get_one(
            {"email": email}
        )