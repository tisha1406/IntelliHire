from fastapi import APIRouter, Depends
from typing import List

from app.auth.jwt_handler import TokenPayload, decode_jwt
from app.rbac.permissions import require_role
from app.rbac.models import UserRole
from app.repositories.audit_log_repository import AuditLogRepository
# pyrefly: ignore [missing-import]
from bson import ObjectId

router = APIRouter(
    prefix="/company/audit-logs",
    tags=["Company - Audit Logs"],
)
audit_repo = AuditLogRepository()

@router.get("/", summary="Get Company Audit Logs")
async def get_audit_logs(
    current_user: TokenPayload = Depends(require_role(UserRole.COMPANY)),
    limit: int = 100,
    skip: int = 0
):
    """
    Retrieve audit logs for the company.
    """
    query = {"company_id": ObjectId(current_user.sub)}
    logs = await audit_repo.get_many(query=query, limit=limit, skip=skip, sort=[("created_at", -1)])
    
    # Format for frontend Activity.jsx
    formatted_logs = []
    for log in logs:
        # Determine logical type for UI icon/color
        resource = log.get("resource", "").lower()
        log_type = "system"
        if "candidate" in resource:
            log_type = "candidate"
        elif "campaign" in resource:
            log_type = "recruitment"
        elif "team" in resource or "auth" in resource:
            log_type = "security"
            
        formatted_logs.append({
            "id": str(log["_id"]),
            "type": log_type,
            "user": log.get("actor_name", "System"),
            "action": log.get("action", ""),
            "target": f"{log.get('resource', '')} ({log.get('resource_id', '')})",
            "time": log.get("created_at").isoformat() if log.get("created_at") else None,
            "details": log.get("details", {})
        })
        
    return formatted_logs
