"""
Notification Service
Handles creation and retrieval of Admin-to-Company notifications.
"""
from datetime import datetime, timezone
from typing import Optional, List

from app.repositories.company_notification_repository import CompanyNotificationRepository
from app.services.audit_service import AuditLogService, AuditLogCreate


class NotificationService:
    def __init__(self):
        self.repo = CompanyNotificationRepository()

    # ------------------------------------------------------------------
    # Admin: create a notification
    # target = "all"        → broadcast to every company
    # target = <company_id> → specific company only
    # ------------------------------------------------------------------
    async def create_notification(
        self,
        *,
        admin_id: str,
        target: str,          # "all" | "<company_id>"
        notification_type: str,   # e.g. "maintenance", "plan_expiry", "announcement"
        title: str,
        message: str,
    ) -> str:
        doc = {
            "target": target,                      # "all" or specific company_id
            "company_id": None if target == "all" else target,
            "type": notification_type,
            "title": title,
            "message": message,
            "is_read": False,
            "created_at": datetime.now(timezone.utc),
            "created_by": admin_id,
        }
        notification_id = await self.repo.create(doc)

        await AuditLogService().log_action(AuditLogCreate(
            user_id=admin_id,
            action="create_notification",
            entity_type="notification",
            entity_id=notification_id,
            details={"target": target, "type": notification_type, "title": title},
        ))

        return notification_id

    # ------------------------------------------------------------------
    # Company: get its own notifications (+ broadcast ones)
    # ------------------------------------------------------------------
    async def get_company_notifications(
        self,
        company_id: str,
        limit: int = 50,
        skip: int = 0,
    ) -> List[dict]:
        return await self.repo.get_for_company(company_id, limit=limit, skip=skip)

    async def count_company_notifications(self, company_id: str) -> int:
        return await self.repo.count_for_company(company_id)

    async def get_unread_count(self, company_id: str) -> int:
        return await self.repo.get_unread_count(company_id)

    async def mark_read(self, notification_id: str) -> bool:
        return await self.repo.mark_read(notification_id)

    async def mark_all_read(self, company_id: str) -> int:
        return await self.repo.mark_all_read(company_id)

    # ------------------------------------------------------------------
    # Admin: get all notifications (paginated)
    # ------------------------------------------------------------------
    async def get_all_notifications(self, limit: int = 50, skip: int = 0) -> List[dict]:
        docs = await self.repo.get_many(query={}, limit=limit, skip=skip)
        # Sort by created_at desc — repo.get_many doesn't sort, use collection directly
        cursor = (
            self.repo.collection
            .find({})
            .sort("created_at", -1)
            .skip(skip)
            .limit(limit)
        )
        return await cursor.to_list(length=limit)

    async def count_all(self) -> int:
        return await self.repo.count()
