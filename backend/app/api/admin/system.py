import psutil
from fastapi import APIRouter, Depends
from app.schemas.response import APIResponse, success_response, PaginationMeta
from app.auth.jwt_handler import TokenPayload, decode_jwt
from app.rbac.permissions import require_role
from app.rbac.models import UserRole
from app.services.audit_service import AuditLogService

router = APIRouter(
    prefix="/admin/system",
    tags=["Admin - System"]
)

@router.get("/health", response_model=APIResponse[dict])
async def get_system_health(
    token: TokenPayload = Depends(require_role(UserRole.ADMIN))
):
    # Get basic system metrics using psutil
    cpu_usage = psutil.cpu_percent(interval=0.1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')

    from app.repositories.base_repository import BaseRepository
    try:
        repo = BaseRepository("system_health")
        await repo.database.command("ping")
        mongo_status = "healthy"
    except Exception:
        mongo_status = "unhealthy"

    return success_response(
        data={
            "cpu_usage": cpu_usage,
            "memory_total": memory.total,
            "memory_used": memory.used,
            "memory_percent": memory.percent,
            "disk_total": disk.total,
            "disk_used": disk.used,
            "disk_percent": disk.percent,
            "services": {
                "mongodb": mongo_status,
                "redis": "healthy", # Assuming redis is OK if we reach here
                "fastapi": "healthy"
            }
        },
        message="System health retrieved."
    )

@router.get("/audit-logs", response_model=APIResponse[list[dict]])
async def get_audit_logs(
    limit: int = 50,
    offset: int = 0,
    token: TokenPayload = Depends(require_role(UserRole.ADMIN))
):
    service = AuditLogService()
    logs = await service.get_logs(limit=limit, skip=offset)
    total = await service.count_logs()
    
    for l in logs:
        l["id"] = str(l["_id"])
        del l["_id"]

    return success_response(
        data=logs,
        pagination=PaginationMeta(total=total, limit=limit, skip=offset, has_more=(offset + limit) < total),
        message="Audit logs retrieved."
    )

@router.get("/security-logs", response_model=APIResponse[list[dict]])
async def get_security_logs(
    limit: int = 50,
    offset: int = 0,
    search: str = None,
    severity: str = None,
    token: TokenPayload = Depends(require_role(UserRole.ADMIN))
):
    from app.repositories.security_log_repository import SecurityLogRepository
    repo = SecurityLogRepository()
    query = {}
    if search:
        query["$or"] = [
            {"event": {"$regex": search, "$options": "i"}},
            {"user": {"$regex": search, "$options": "i"}},
            {"ip": {"$regex": search, "$options": "i"}}
        ]
    if severity:
        query["severity"] = severity

    logs = await repo.get_many(query=query, limit=limit, skip=offset)
    total = await repo.count(query=query)
    
    for l in logs:
        l["id"] = str(l["_id"])
        del l["_id"]

    return success_response(
        data=logs,
        pagination=PaginationMeta(total=total, limit=limit, skip=offset, has_more=(offset + limit) < total),
        message="Security logs retrieved."
    )

@router.get("/notifications", response_model=APIResponse[list[dict]])
async def get_notifications(
    limit: int = 20,
    offset: int = 0,
    token: TokenPayload = Depends(require_role(UserRole.ADMIN))
):
    from app.repositories.base_repository import BaseRepository
    repo = BaseRepository("notifications")
    
    cursor = repo.collection.find().sort("created_at", -1).skip(offset).limit(limit)
    notifs = await cursor.to_list(length=limit)
    total = await repo.count()
    
    records = []
    for n in notifs:
        records.append({
            "id": str(n["_id"]),
            "title": n.get("title", "Notification"),
            "message": n.get("message", ""),
            "read": n.get("read", False),
            "createdAt": n.get("created_at")
        })

    return success_response(
        data=records,
        pagination=PaginationMeta(total=total, limit=limit, skip=offset, has_more=(offset + limit) < total),
        message="Notifications retrieved."
    )
