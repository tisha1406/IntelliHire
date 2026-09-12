from app.repositories.base_repository import BaseRepository
from bson import ObjectId
from app.ai_interview.core.enums import InterviewModeStatus


class InterviewModeRepository(BaseRepository):

    def __init__(self):
        super().__init__("interview_mode_definitions")

    async def update(self, document_id: str, update_data: dict) -> bool:
        query = {
            "_id": ObjectId(document_id),
            "status": {"$ne": InterviewModeStatus.PUBLISHED}
        }
        result = await self.collection.update_one(query, {"$set": update_data})
        if result.matched_count == 0:
            existing = await self.get_by_id(document_id)
            if existing:
                raise ValueError("Cannot modify a published interview mode. Create a new version instead.")
            raise ValueError("Document not found.")
        return result.modified_count > 0

    async def delete(self, document_id: str) -> bool:
        query = {
            "_id": ObjectId(document_id),
            "status": {"$ne": InterviewModeStatus.PUBLISHED}
        }
        result = await self.collection.delete_one(query)
        if result.deleted_count == 0:
            existing = await self.get_by_id(document_id)
            if existing:
                raise ValueError("Cannot delete a published interview mode.")
            raise ValueError("Document not found.")
        return True

    async def get_by_mode_id(
        self,
        mode_id: str,
        status: InterviewModeStatus = InterviewModeStatus.PUBLISHED,
    ):
        """
        Look up an interview mode definition by its business-key mode_id string.

        InterviewCampaign.interview_mode stores the mode_id string, not the MongoDB
        ObjectId, so get_by_id() cannot be used for this purpose.
        """
        return await self.get_one({"mode_id": mode_id, "status": status.value})