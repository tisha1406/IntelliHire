from app.repositories.base_repository import BaseRepository


class InterviewSessionRepository(BaseRepository):

    def __init__(self):
        super().__init__("interview_sessions")

    async def get_by_candidate(self, candidate_id: str):
        return await self.get_many(
            {"candidate_id": candidate_id}
        )

    async def get_by_session_id(self, session_id: str):
        """Looks up a raw interview_sessions document by its engine-assigned
        session_id field -- the real AI interview engine's own identifier
        (set by SessionInitializer), distinct from Mongo's auto-generated
        _id. BaseRepository.get_by_id() queries by _id and is not usable for
        session_id-keyed lookups (session_id is not a valid ObjectId)."""
        return await self.get_one({"session_id": session_id})