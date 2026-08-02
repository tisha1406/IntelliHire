from fastapi import APIRouter, Depends
from app.schemas.response import APIResponse, success_response
from app.auth.jwt_handler import TokenPayload, decode_jwt
from app.rbac.permissions import require_role
from app.rbac.models import UserRole
from app.services.dashboard_service import DashboardService
from app.repositories.user_repository import UserRepository

router = APIRouter(
    prefix="/admin/dashboard",
    tags=["Admin - Dashboard"]
)

@router.get("", response_model=APIResponse[dict])
async def get_dashboard(
    token: TokenPayload = Depends(require_role(UserRole.ADMIN))
):
    service = DashboardService()
    user_repo = UserRepository()
    
    # Get user details for welcome payload
    user = await user_repo.get_by_id(token.sub)
    if not user:
        user = {"name": "Admin", "role": "SUPER_ADMIN"}

    data = await service.get_dashboard_data(user)
    
    return success_response(
        data=data,
        message="Dashboard data retrieved successfully."
    )
