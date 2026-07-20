from app.repositories.base_repository import BaseRepository


class CompanyRepository(BaseRepository):

    def __init__(self):
        super().__init__("companies")

    async def get_by_email(self, email: str):
        return await self.get_one(
            {"contact_email": email}
        )

    async def get_active_companies(self):
        return await self.get_many(
            {"status": "active"}
        )