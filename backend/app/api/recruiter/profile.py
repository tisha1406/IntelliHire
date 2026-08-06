from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, UTC

from app.auth.jwt_handler import TokenPayload, hash_password
from app.rbac.permissions import require_recruiter_scope
from app.schemas.response import APIResponse, success_response
from app.repositories.recruiter_repository import RecruiterRepository
from app.repositories.user_repository import UserRepository

router = APIRouter(
    prefix="/profile",
    tags=["Recruiter - Profile"]
)

class ProfileUpdateRequest(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None

class ChangePasswordRequest(BaseModel):
    current_password: Optional[str] = None
    new_password: str

@router.get("/", response_model=APIResponse[dict])
async def get_profile(
    token: TokenPayload = Depends(require_recruiter_scope)
):
    repo = RecruiterRepository()
    profile = await repo.get_by_id(token.recruiter_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
        
    profile["id"] = str(profile["_id"])
    profile.pop("_id", None)
    return success_response(data=profile)

@router.put("/", response_model=APIResponse[dict])
async def update_profile(
    request: ProfileUpdateRequest,
    token: TokenPayload = Depends(require_recruiter_scope)
):
    repo = RecruiterRepository()
    update_data = {k: v for k, v in request.dict().items() if v is not None}
    if not update_data:
        return success_response(message="Nothing to update")
        
    update_data["updated_at"] = datetime.now(UTC)
    await repo.update(token.recruiter_id, update_data)
    
    return success_response(message="Profile updated successfully")

@router.post("/change-password", response_model=APIResponse[dict])
async def change_password(
    request: ChangePasswordRequest,
    token: TokenPayload = Depends(require_recruiter_scope)
):
    user_repo = UserRepository()
    user = await user_repo.get_by_id(token.sub)
    if not user:
        raise HTTPException(status_code=404, detail="User account not found")
        
    hashed_pwd = hash_password(request.new_password)
    
    await user_repo.update(token.sub, {
        "password_hash": hashed_pwd,
        "must_change_password": False,
        "updated_at": datetime.now(UTC)
    })
    
    return success_response(message="Password changed successfully")
