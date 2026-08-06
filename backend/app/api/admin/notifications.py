"""
Admin Notifications API
Allows the Super Admin to create and view system notifications.
Notifications can target all companies or a specific company.
"""
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from typing import Optional

from app.schemas.response import APIResponse, success_response, PaginationMeta
from app.auth.jwt_handler import TokenPayload
from app.rbac.permissions import require_role
from app.rbac.models import UserRole
from app.services.notification_service import NotificationService
from app.db.mongo import serialize_mongo_doc

router = APIRouter(
    prefix="/admin/notifications",
    tags=["Admin - Notifications"],
)


class CreateNotificationRequest(BaseModel):
    target: str = "all"                  # "all" | "<company_id>"
    type: str = "announcement"           # "maintenance" | "plan_expiry" | "announcement"
    title: str
    message: str


# ──────────────────────────────────────────────────────────────────────
# GET /admin/notifications
# ──────────────────────────────────────────────────────────────────────

@router.get("", response_model=APIResponse[list[dict]])
async def get_notifications(
    limit: int = Query(50, ge=1),
    offset: int = Query(0, ge=0),
    token: TokenPayload = Depends(require_role(UserRole.ADMIN)),
):
    """Return all notifications created by admin (paginated)."""
    service = NotificationService()
    notifications = await service.get_all_notifications(limit=limit, skip=offset)
    total = await service.count_all()

    serialized = serialize_mongo_doc(notifications)

    return success_response(
        data=serialized,
        pagination=PaginationMeta(
            total=total,
            limit=limit,
            skip=offset,
            has_more=(offset + limit) < total,
        ),
        message="Notifications retrieved successfully.",
    )


# ──────────────────────────────────────────────────────────────────────
# POST /admin/notifications
# ──────────────────────────────────────────────────────────────────────

@router.post("", response_model=APIResponse[dict])
async def create_notification(
    request: CreateNotificationRequest,
    token: TokenPayload = Depends(require_role(UserRole.ADMIN)),
):
    """
    Create a notification.
    - target="all"       → broadcast to every company
    - target=<company_id> → send to one specific company
    """
    service = NotificationService()
    notification_id = await service.create_notification(
        admin_id=token.sub,
        target=request.target,
        notification_type=request.type,
        title=request.title,
        message=request.message,
    )
    return success_response(
        data={"notification_id": notification_id},
        message="Notification created successfully.",
    )


# ──────────────────────────────────────────────────────────────────────
# PATCH /admin/notifications/{notification_id}/read
# ──────────────────────────────────────────────────────────────────────

@router.patch("/{notification_id}/read", response_model=APIResponse[dict])
async def mark_notification_read(
    notification_id: str,
    token: TokenPayload = Depends(require_role(UserRole.ADMIN)),
):
    """Mark a notification as read."""
    service = NotificationService()
    success = await service.mark_read(notification_id)
    if not success:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Notification not found.")
    return success_response(
        data={"id": notification_id, "is_read": True},
        message="Notification marked as read.",
    )
