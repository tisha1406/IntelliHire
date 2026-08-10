"""
Company User Profile endpoints.
Allows the authenticated company-role user to read and update their own profile.
"""
from datetime import UTC, datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from passlib.context import CryptContext
from pydantic import BaseModel

from app.auth.jwt_handler import TokenPayload
from app.rbac.models import UserRole
from app.rbac.permissions import require_role, require_company_or_recruiter
from app.repositories.company_repository import CompanyRepository
from app.repositories.user_repository import UserRepository

pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")

router = APIRouter(
    prefix="/company/profile",
    tags=["Company - Profile"],
)

user_repo = UserRepository()
company_repo = CompanyRepository()


class CompanyProfileResponse(BaseModel):
    id: str
    company_name: str
    logo: Optional[str] = None
    industry: Optional[str] = None
    subscription: Optional[dict] = None
    contact_email: Optional[str] = None
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    status: Optional[str] = None
    features: Optional[dict] = None
    usage: Optional[dict] = None
    limits: Optional[dict] = None


class ProfileUpdateRequest(BaseModel):
    company_name: Optional[str] = None
    industry: Optional[str] = None
    contact_email: Optional[str] = None
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None


class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str
    confirm_password: str


@router.get("", response_model=CompanyProfileResponse, summary="Get Current Company Profile")
async def get_profile(
    current_user: TokenPayload = Depends(require_company_or_recruiter),
):
    """
    Return the profile of the company workspace.
    - Company Admin: company_id == sub
    - Recruiter: company_id comes from token.company_id
    Both roles share the same Company Workspace; data is scoped by company_id.
    """
    # Resolve company_id based on role
    if current_user.role.upper() == UserRole.RECRUITER.value.upper():
        resolved_company_id = current_user.company_id
    else:
        resolved_company_id = current_user.sub

    if not resolved_company_id:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="company_id not found in token.")

    company = await company_repo.get_by_id(resolved_company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found.")

    general = company.get("general", {})
    company_name = (
        company.get("company_name") or general.get("name") or company.get("name") or ""
    )

    return CompanyProfileResponse(
        id=str(company["_id"]),
        company_name=company_name,
        logo=general.get("logo_url") or company.get("logo"),
        industry=general.get("industry") or company.get("industry"),
        subscription=company.get("subscription", {}),
        contact_email=general.get("contact_email") or company.get("contact_email"),
        contact_person=general.get("contact_person") or company.get("contact_person"),
        phone=general.get("phone") or company.get("phone"),
        website=general.get("website") or company.get("website"),
        status=company.get("status"),
        features=company.get("features", {}),
        usage=company.get("usage", {}),
        limits=company.get("limits", {}),
    )


@router.patch("", response_model=CompanyProfileResponse, summary="Update Current Company Profile")
async def update_profile(
    payload: ProfileUpdateRequest,
    current_user: TokenPayload = Depends(require_role(UserRole.COMPANY)),
):
    """
    Update editable profile fields for the authenticated company.
    """
    updates = {k: v for k, v in payload.dict().items() if v is not None}
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update.")

    updates["updated_at"] = datetime.now(UTC)

    success = await company_repo.update(current_user.sub, updates)
    if not success:
        raise HTTPException(status_code=404, detail="Company not found.")

    return await get_profile(current_user)


@router.post("/change-password", summary="Change Password")
async def change_password(
    payload: PasswordChangeRequest,
    current_user: TokenPayload = Depends(require_role(UserRole.COMPANY)),
):
    """
    Verify current password, then update to a new password.
    """
    company = await company_repo.get_by_id(current_user.sub)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found.")

    creds = company.get("credentials", {})
    hashed = creds.get("password_hash", "")
    if not hashed or not pwd_ctx.verify(payload.current_password, hashed):
        raise HTTPException(status_code=400, detail="Current password is incorrect.")

    if payload.new_password != payload.confirm_password:
        raise HTTPException(status_code=400, detail="New passwords do not match.")

    if len(payload.new_password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters.")

    new_hash = pwd_ctx.hash(payload.new_password)
    await company_repo.update(
        current_user.sub,
        {
            "credentials": {**creds, "password_hash": new_hash},
            "updated_at": datetime.now(UTC),
        },
    )

    return {"message": "Password updated successfully."}
