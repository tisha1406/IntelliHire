from app.repositories.base_repository import BaseRepository


class InterviewReportRepository(BaseRepository):

    def __init__(self):
        super().__init__("interview_reports")

    async def get_by_session(self, session_id: str):
        return await self.get_one(
            {"session_id": session_id}
        )