from app.repositories.base_repository import BaseRepository


class ReportRepository(BaseRepository):
    """
    Repository for managing generated hiring reports in MongoDB.
    """

    def __init__(self):
        super().__init__("reports")
