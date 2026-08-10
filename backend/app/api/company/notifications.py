"""
Company Notifications API
Provides the authenticated company access to its own notifications.
All queries derive company_id from the JWT — never from the request body.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import Optional

from app.auth.jwt_handler import TokenPayload
from app.rbac.models import UserRole
from app.rbac.permissions import require_company_or_recruiter
from app.schemas.response import APIResponse, success_response, PaginationMeta
from app.services.notification_service import NotificationService
from app.db.mongo import serialize_mongo_doc

router = APIRouter(
    prefix="/company/notifications",
    tags=["Company - Notifications"],
)


# ──────────────────────────────────────────────────────────────────────
# GET /company/notifications
# ──────────────────────────────────────────────────────────────────────
@router.get("", response_model=APIResponse[list[dict]])
async def get_notifications(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: TokenPayload = Depends(require_company_or_recruiter),
):
    """
    Return paginated notifications for the authenticated company workspace.
    Both Company Admins and Recruiters in the same workspace share notifications.
    Includes notifications targeted at this company and broadcast ('all') notifications.
    """
    # Resolve company_id by role
    company_id = (
        current_user.company_id
        if current_user.role.upper() == UserRole.RECRUITER.value.upper()
        else current_user.sub
    )
    service = NotificationService()
    notifications = await service.get_company_notifications(
        company_id=company_id,
        limit=limit,
        skip=offset,
    )
    total = await service.count_company_notifications(company_id)
    unread = await service.get_unread_count(company_id)

    serialized = serialize_mongo_doc(notifications)

    return success_response(
        data=serialized,
        pagination=PaginationMeta(
            total=total,
            limit=limit,
            skip=offset,
            has_more=(offset + limit) < total,
        ),
        message=f"Notifications retrieved. Unread: {unread}",
    )


# ──────────────────────────────────────────────────────────────────────
# PATCH /company/notifications/{notification_id}/read
# ──────────────────────────────────────────────────────────────────────
@router.patch("/{notification_id}/read", response_model=APIResponse[dict])
async def mark_notification_read(
    notification_id: str,
    current_user: TokenPayload = Depends(require_company_or_recruiter),
):
    """Mark a single notification as read."""
    service = NotificationService()
    success = await service.mark_read(notification_id)
    if not success:
        raise HTTPException(status_code=404, detail="Notification not found.")
    return success_response(data={"id": notification_id, "is_read": True}, message="Notification marked as read.")


# ──────────────────────────────────────────────────────────────────────
# POST /company/notifications/read-all
# ──────────────────────────────────────────────────────────────────────
@router.post("/read-all", response_model=APIResponse[dict])
async def mark_all_read(
    current_user: TokenPayload = Depends(require_company_or_recruiter),
):
    """Mark all of this company's notifications as read."""
    company_id = (
        current_user.company_id
        if current_user.role.upper() == UserRole.RECRUITER.value.upper()
        else current_user.sub
    )
    service = NotificationService()
    updated = await service.mark_all_read(company_id)
    return success_response(data={"updated": updated}, message="All notifications marked as read.")
