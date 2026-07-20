from app.repositories.base_repository import BaseRepository


class InterviewSessionRepository(BaseRepository):

    def __init__(self):
        super().__init__("interview_sessions")

    async def get_by_candidate(self, candidate_id: str):
        return await self.get_many(
            {"candidate_id": candidate_id}
        )