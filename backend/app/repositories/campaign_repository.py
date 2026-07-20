from app.repositories.base_repository import BaseRepository


class CampaignRepository(BaseRepository):

    def __init__(self):
        super().__init__("interview_campaigns")

    async def get_by_company(self, company_id: str):
        return await self.get_many(
            {"company_id": company_id}
        )