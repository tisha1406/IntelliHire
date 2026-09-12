from app.repositories.base_repository import BaseRepository


class InterviewTurnRepository(BaseRepository):

    def __init__(self):
        super().__init__("interview_turns")

    async def get_by_session(self, session_id: str):
        return await self.get_many(
            {"session_id": session_id}
        )
