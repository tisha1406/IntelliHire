"""
Company Notification Repository
Manages notifications sent by Admin to Company accounts.
Collection: company_notifications
"""
from typing import List, Optional
from bson import ObjectId
from app.repositories.base_repository import BaseRepository


class CompanyNotificationRepository(BaseRepository):

    def __init__(self):
        super().__init__("company_notifications")

    # ------------------------------------------------------------------
    # Fetch notifications for a specific company (includes broadcast ones)
    # ------------------------------------------------------------------
    async def get_for_company(
        self,
        company_id: str,
        limit: int = 50,
        skip: int = 0,
    ) -> List[dict]:
        """
        Return notifications targeted at this company or broadcast to all companies.
        Sorted newest-first.
        """
        query = {
            "$or": [
                {"company_id": company_id},
                {"target": "all"},
            ]
        }
        cursor = (
            self.collection
            .find(query)
            .sort("created_at", -1)
            .skip(skip)
            .limit(limit)
        )
        return await cursor.to_list(length=limit)

    async def count_for_company(self, company_id: str) -> int:
        return await self.collection.count_documents({
            "$or": [
                {"company_id": company_id},
                {"target": "all"},
            ]
        })

    # ------------------------------------------------------------------
    # Unread count
    # ------------------------------------------------------------------
    async def get_unread_count(self, company_id: str) -> int:
        return await self.collection.count_documents({
            "$or": [
                {"company_id": company_id},
                {"target": "all"},
            ],
            "is_read": False,
        })

    # ------------------------------------------------------------------
    # Mark one notification as read for a company
    # ------------------------------------------------------------------
    async def mark_read(self, notification_id: str) -> bool:
        result = await self.collection.update_one(
            {"_id": ObjectId(notification_id)},
            {"$set": {"is_read": True}},
        )
        return result.modified_count > 0

    # ------------------------------------------------------------------
    # Mark all as read for a company
    # ------------------------------------------------------------------
    async def mark_all_read(self, company_id: str) -> int:
        result = await self.collection.update_many(
            {
                "$or": [
                    {"company_id": company_id},
                    {"target": "all"},
                ],
                "is_read": False,
            },
            {"$set": {"is_read": True}},
        )
        return result.modified_count
