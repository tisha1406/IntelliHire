from fastapi import APIRouter, Depends
from app.schemas.response import APIResponse, success_response
from app.auth.jwt_handler import TokenPayload, decode_jwt
from app.rbac.permissions import require_role
from app.rbac.models import UserRole

router = APIRouter(
    prefix="/admin/storage",
    tags=["Admin - Storage"]
)

@router.get("", response_model=APIResponse[dict])
async def get_storage_metrics(
    token: TokenPayload = Depends(require_role(UserRole.ADMIN))
):
    # This is a mocked response for the UI layer as requested.
    # In a real scenario, this would query S3/Blob storage metrics or the database.
    data = {
        "platform_storage": {
            "total_used_gb": 2.3,
            "total_capacity_gb": 10.0,
            "breakdown": {
                "companies": 0.5,
                "vector_storage": 0.8,
                "reports": 0.2,
                "voice_files": 0.6,
                "resume_storage": 0.2
            }
        }
    }
    
    return success_response(
        data=data,
        message="Storage metrics retrieved successfully."
    )
