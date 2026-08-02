from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app.schemas.response import APIResponse, success_response
from app.auth.jwt_handler import TokenPayload, decode_jwt
from app.rbac.permissions import require_role
from app.rbac.models import UserRole
from app.repositories.user_repository import UserRepository

router = APIRouter(
    prefix="/admin/profile",
    tags=["Admin - Profile"]
)

class UpdateProfileRequest(BaseModel):
    name: str | None = None
    phone: str | None = None
    avatar: str | None = None
    language: str | None = None
    timezone: str | None = None

@router.get("", response_model=APIResponse[dict])
async def get_profile(
    token: TokenPayload = Depends(require_role(UserRole.ADMIN))
):
    user_repo = UserRepository()
    user = await user_repo.get_by_id(token.sub)
    
    if not user:
        return success_response(
            data={"name": "Administrator", "role": "SUPER_ADMIN"},
            message="Default profile retrieved."
        )

    return success_response(
        data={
            "id": str(user["_id"]),
            "name": user.get("name"),
            "email": user.get("email"),
            "phone": user.get("phone", ""),
            "avatar": user.get("avatar", ""),
            "language": user.get("language", "en-US"),
            "timezone": user.get("timezone", "UTC"),
            "role": user.get("role")
        },
        message="Profile retrieved successfully."
    )

@router.put("", response_model=APIResponse[dict])
async def update_profile(
    request: UpdateProfileRequest,
    token: TokenPayload = Depends(require_role(UserRole.ADMIN))
):
    user_repo = UserRepository()
    
    update_data = {}
    if request.name is not None: update_data["name"] = request.name
    if request.phone is not None: update_data["phone"] = request.phone
    if request.avatar is not None: update_data["avatar"] = request.avatar
    if request.language is not None: update_data["language"] = request.language
    if request.timezone is not None: update_data["timezone"] = request.timezone
        
    await user_repo.update(token.sub, update_data)
    
    return success_response(message="Profile updated successfully.")
