from app.repositories.base_repository import BaseRepository


class ExportRepository(BaseRepository):
    """
    Repository for managing export history and generated downloads in MongoDB.
    """

    def __init__(self):
        super().__init__("exports")
