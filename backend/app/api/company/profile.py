"""
Company User Profile endpoints.
Allows the authenticated company-role user to read and update their own profile.
"""
from datetime import datetime, UTC
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from passlib.context import CryptContext
from pydantic import BaseModel

from app.repositories.user_repository import UserRepository
from app.rbac.permissions import require_role
from app.auth.jwt_handler import TokenPayload
from app.rbac.models import UserRole

pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")

router = APIRouter(
    prefix="/company/profile",
    tags=["Company - Profile"],
)

user_repo = UserRepository()


# ─── Schemas ──────────────────────────────────────────────────
class ProfileResponse(BaseModel):
    id: str
    name: str
    email: str
    phone: Optional[str] = ""
    location: Optional[str] = ""
    linkedin: Optional[str] = ""
    title: Optional[str] = ""
    department: Optional[str] = ""
    bio: Optional[str] = ""
    joined_date: Optional[str] = ""


class ProfileUpdateRequest(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    linkedin: Optional[str] = None
    title: Optional[str] = None
    department: Optional[str] = None
    bio: Optional[str] = None


class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str
    confirm_password: str


# ─── Endpoints ────────────────────────────────────────────────
@router.get("", response_model=ProfileResponse, summary="Get Current User Profile")
async def get_profile(
    current_user: TokenPayload = Depends(require_role(UserRole.COMPANY)),
):
    """
    Return the profile of the currently authenticated user.
    """
    user = await user_repo.get_by_id(current_user.sub)
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    # Format joined date
    created = user.get("created_at")
    if isinstance(created, datetime):
        joined_date = created.strftime("%B %Y")
    else:
        joined_date = ""

    return ProfileResponse(
        id=str(user["_id"]),
        name=user.get("name", ""),
        email=user.get("email", ""),
        phone=user.get("phone", ""),
        location=user.get("location", ""),
        linkedin=user.get("linkedin", ""),
        title=user.get("title", ""),
        department=user.get("department", ""),
        bio=user.get("bio", ""),
        joined_date=joined_date,
    )


@router.patch("", response_model=ProfileResponse, summary="Update Current User Profile")
async def update_profile(
    payload: ProfileUpdateRequest,
    current_user: TokenPayload = Depends(require_role(UserRole.COMPANY)),
):
    """
    Update editable profile fields for the authenticated user.
    """
    updates = {k: v for k, v in payload.dict().items() if v is not None}
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update.")

    updates["updated_at"] = datetime.now(UTC)

    success = await user_repo.update(current_user.sub, updates)
    if not success:
        raise HTTPException(status_code=404, detail="User not found.")

    # Return updated profile
    return await get_profile(current_user)


@router.post("/change-password", summary="Change Password")
async def change_password(
    payload: PasswordChangeRequest,
    current_user: TokenPayload = Depends(require_role(UserRole.COMPANY)),
):
    """
    Verify current password, then update to a new password.
    """
    user = await user_repo.get_by_id(current_user.sub)
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    # Verify current password
    hashed = user.get("password_hash") or user.get("hashed_password") or user.get("password", "")
    if not hashed or not pwd_ctx.verify(payload.current_password, hashed):
        raise HTTPException(status_code=400, detail="Current password is incorrect.")

    if payload.new_password != payload.confirm_password:
        raise HTTPException(status_code=400, detail="New passwords do not match.")

    if len(payload.new_password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters.")

    new_hash = pwd_ctx.hash(payload.new_password)
    await user_repo.update(current_user.sub, {
        "password_hash": new_hash,
        "updated_at": datetime.now(UTC),
    })

    return {"message": "Password updated successfully."}
