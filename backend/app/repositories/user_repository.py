from app.repositories.base_repository import BaseRepository


class UserRepository(BaseRepository):

    def __init__(self):
        super().__init__("users")

    async def get_by_email(self, email: str):
        return await self.get_one(
            {"email": email}
        )