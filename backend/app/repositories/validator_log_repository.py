from app.repositories.base_repository import BaseRepository


class ValidatorLogRepository(BaseRepository):

    def __init__(self):
        super().__init__("validator_logs")

    async def get_by_session(self, session_id: str):
        return await self.get_many(
            {"session_id": session_id}
        )