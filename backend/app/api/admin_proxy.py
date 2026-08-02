from datetime import datetime, timezone, timedelta
from bson import ObjectId
from fastapi import APIRouter, Depends, status, HTTPException

from app.schemas.response import APIResponse, success_response
from app.services.analytics_service import AnalyticsService
from app.repositories.platform_settings_repository import PlatformSettingsRepository
from app.repositories.user_repository import UserRepository
from app.repositories.company_repository import CompanyRepository
from app.repositories.recruiter_repository import RecruiterRepository
from app.repositories.candidate_repository import CandidateRepository
from app.repositories.interview_session_repository import InterviewSessionRepository
from app.db.mongo import get_database
from app.auth.jwt_handler import TokenPayload
from app.rbac.permissions import require_role
from app.rbac.models import UserRole

router = APIRouter(
    prefix="/api/admin",
    tags=["Admin - Proxy"]
)

NOTIFICATIONS_COLLECTION = "admin_notifications"

async def seed_notifications_if_empty():
    db = get_database()
    collection = db[NOTIFICATIONS_COLLECTION]
    count = await collection.count_documents({})
    if count == 0:
        now = datetime.now(timezone.utc)
        await collection.insert_many([
            {
                "title": "System Update",
                "message": "Backend updated successfully.",
                "read": False,
                "createdAt": now.isoformat(),
                "type": "system",
                "link": None
            },
            {
                "title": "New Company Registration",
                "message": "TechNova joined the platform.",
                "read": False,
                "createdAt": (now - timedelta(hours=1)).isoformat(),
                "type": "company",
                "link": "/admin/companies"
            },
            {
                "title": "Interview Scheduled",
                "message": "Sarah Jenkins • Tomorrow 10:00 AM.",
                "read": True,
                "createdAt": (now - timedelta(hours=2)).isoformat(),
                "type": "interview",
                "link": "/admin/interviews"
            }
        ])

@router.get("/dashboard", response_model=APIResponse[dict])
async def get_admin_dashboard(
    token: TokenPayload = Depends(require_role(UserRole.ADMIN))
):
    service = AnalyticsService()
    dashboard = await service.get_dashboard_stats(current_user_id=token.sub)
    return success_response(data=dashboard, message="Admin dashboard retrieved successfully.")

@router.get("/search", response_model=APIResponse[dict])
async def global_search(
    q: str,
    token: TokenPayload = Depends(require_role(UserRole.ADMIN))
):
    company_repo = CompanyRepository()
    user_repo = UserRepository()
    recruiter_repo = RecruiterRepository()
    candidate_repo = CandidateRepository()
    interview_repo = InterviewSessionRepository()

    search_filter = {"$regex": q, "$options": "i"}
    companies = await company_repo.get_many(
        query={"$or": [{"name": search_filter}, {"contact_email": search_filter}, {"industry": search_filter}]},
        limit=5
    )
    users = await user_repo.get_many(
        query={"$or": [{"name": search_filter}, {"email": search_filter}]},
        limit=5
    )
    recruiters = await recruiter_repo.get_many(
        query={"$or": [{"name": search_filter}, {"email": search_filter}]},
        limit=5
    )
    candidates = await candidate_repo.get_many(
        query={"$or": [{"name": search_filter}, {"email": search_filter}]},
        limit=5
    )
    interviews = await interview_repo.get_many(
        query={"$or": [{"title": search_filter}, {"status": search_filter}]},
        limit=5
    )

    return success_response(
        data={
            "companies": [{"id": str(c["_id"]), "name": c.get("general", {}).get("name"), "type": "company"} for c in companies],
            "users": [{"id": str(u["_id"]), "name": u.get("name"), "type": "user"} for u in users],
            "recruiters": [{"id": str(r["_id"]), "name": r.get("name"), "type": "recruiter"} for r in recruiters],
            "candidates": [{"id": str(c["_id"]), "name": c.get("name"), "type": "candidate"} for c in candidates],
            "interviews": [{"id": str(i["_id"]), "title": i.get("title"), "status": i.get("status"), "type": "interview"} for i in interviews]
        },
        message="Search results retrieved successfully."
    )

@router.get("/settings", response_model=APIResponse[dict])
async def get_admin_settings(
    token: TokenPayload = Depends(require_role(UserRole.ADMIN))
):
    repo = PlatformSettingsRepository()
    settings = await repo.get_settings()
    if settings is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Platform settings not found.")
    return success_response(data=settings, message="Admin settings retrieved successfully.")

@router.put("/settings", response_model=APIResponse[dict])
async def update_admin_settings(
    request: dict,
    token: TokenPayload = Depends(require_role(UserRole.ADMIN))
):
    repo = PlatformSettingsRepository()
    payload = {k: v for k, v in request.items() if v is not None}
    if not payload:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No settings provided for update.")
    await repo.update_settings(payload)
    updated = await repo.get_settings()
    return success_response(data=updated, message="Admin settings updated successfully.")

@router.get("/profile", response_model=APIResponse[dict])
async def get_admin_profile(
    token: TokenPayload = Depends(require_role(UserRole.ADMIN))
):
    repo = UserRepository()
    user = await repo.get_by_id(token.sub)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Admin profile not found.")
    return success_response(
        data={
            "id": str(user.get("_id")),
            "name": user.get("name", "Administrator"),
            "email": user.get("email", ""),
            "role": user.get("role", "ADMIN"),
            "phone": user.get("phone", ""),
            "avatar": user.get("avatar", ""),
            "language": user.get("language", "en-US"),
            "timezone": user.get("timezone", "UTC"),
            "last_login": user.get("last_login")
                and user.get("last_login").isoformat()
        },
        message="Admin profile retrieved successfully."
    )

@router.put("/profile", response_model=APIResponse[dict])
async def update_admin_profile(
    request: dict,
    token: TokenPayload = Depends(require_role(UserRole.ADMIN))
):
    repo = UserRepository()
    user = await repo.get_by_id(token.sub)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Admin profile not found.")

    payload = {k: v for k, v in request.items() if k in {"name", "phone", "avatar", "language", "timezone"} and v is not None}
    if not payload:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No profile updates provided.")

    await repo.update(str(user.get("_id")), payload)
    updated_user = await repo.get_by_id(token.sub)

    return success_response(
        data={
            "id": str(updated_user.get("_id")),
            "name": updated_user.get("name", "Administrator"),
            "email": updated_user.get("email", ""),
            "role": updated_user.get("role", "ADMIN"),
            "phone": updated_user.get("phone", ""),
            "avatar": updated_user.get("avatar", ""),
            "language": updated_user.get("language", "en-US"),
            "timezone": updated_user.get("timezone", "UTC"),
            "last_login": updated_user.get("last_login")
                and updated_user.get("last_login").isoformat()
        },
        message="Admin profile updated successfully."
    )

@router.get("/notifications", response_model=APIResponse[list[dict]])
async def get_admin_notifications(
    token: TokenPayload = Depends(require_role(UserRole.ADMIN))
):
    await seed_notifications_if_empty()
    db = get_database()
    collection = db[NOTIFICATIONS_COLLECTION]
    notifications = await collection.find({}, sort=[("createdAt", -1)]).to_list(length=50)
    for n in notifications:
        n["id"] = str(n["_id"])
        n.pop("_id", None)
    return success_response(data=notifications, message="Notifications retrieved successfully.")

@router.post("/notifications/{notification_id}/read", response_model=APIResponse[dict])
async def mark_notification_read(
    notification_id: str,
    token: TokenPayload = Depends(require_role(UserRole.ADMIN))
):
    db = get_database()
    collection = db[NOTIFICATIONS_COLLECTION]
    result = await collection.update_one(
        {"_id": ObjectId(notification_id)},
        {"$set": {"read": True}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found.")
    return success_response(message="Notification marked read.")

@router.post("/notifications/read-all", response_model=APIResponse[dict])
async def mark_all_notifications_read(
    token: TokenPayload = Depends(require_role(UserRole.ADMIN))
):
    db = get_database()
    collection = db[NOTIFICATIONS_COLLECTION]
    await collection.update_many({}, {"$set": {"read": True}})
    return success_response(message="All notifications marked as read.")

@router.delete("/notifications/{notification_id}", response_model=APIResponse[dict])
async def delete_notification(
    notification_id: str,
    token: TokenPayload = Depends(require_role(UserRole.ADMIN))
):
    db = get_database()
    collection = db[NOTIFICATIONS_COLLECTION]
    result = await collection.delete_one({"_id": ObjectId(notification_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found.")
    return success_response(message="Notification deleted successfully.")
