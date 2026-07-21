from app.repositories.base_repository import BaseRepository


class InterviewModeRepository(BaseRepository):

    def __init__(self):
        super().__init__("interview_modes")