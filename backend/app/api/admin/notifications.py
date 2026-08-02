from fastapi import APIRouter, Depends
from datetime import datetime, timezone
from app.schemas.response import APIResponse, success_response
from app.auth.jwt_handler import TokenPayload, decode_jwt
from app.rbac.permissions import require_role
from app.rbac.models import UserRole

router = APIRouter(
    prefix="/admin/notifications",
    tags=["Admin - Notifications"]
)

@router.get("", response_model=APIResponse[list[dict]])
async def get_notifications(
    token: TokenPayload = Depends(require_role(UserRole.ADMIN))
):
    # Mocking notifications as requested by the plan
    mock_notifications = [
        {
            "id": "1",
            "title": "New Company Registered",
            "message": "TechCorp Inc. has joined the platform.",
            "is_read": False,
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "2",
            "title": "High Server Load",
            "message": "CPU usage exceeded 80% on the backend server.",
            "is_read": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
    ]
    
    return success_response(
        data=mock_notifications,
        message="Notifications retrieved successfully."
    )
