from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, UTC
import random
import string

from app.auth.jwt_handler import TokenPayload, hash_password
from app.rbac.permissions import require_own_company, require_role
from app.rbac.models import UserRole
from app.schemas.response import APIResponse, success_response
from app.repositories.recruiter_repository import RecruiterRepository
from app.repositories.user_repository import UserRepository

router = APIRouter(
    prefix="/recruiters",
    tags=["Company - Recruiters"]
)

# Schemas
class RecruiterCreateRequest(BaseModel):
    first_name: str
    last_name: str
    email: str
    phone: str
    department: str
    designation: str
    role: str = "Recruiter"
    status: str = "active"

class RecruiterUpdateRequest(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    department: Optional[str] = None
    designation: Optional[str] = None
    status: Optional[str] = None

def generate_temp_password(length=12):
    chars = string.ascii_letters + string.digits + "!@#$%^&*"
    return "".join(random.choice(chars) for _ in range(length))

@router.get("/", response_model=APIResponse[list])
async def get_company_recruiters(
    company_id: str,
    token: TokenPayload = Depends(require_own_company)
):
    repo = RecruiterRepository()
    recruiters = await repo.get_many({"company_id": company_id})
    for r in recruiters:
        r["id"] = str(r["_id"])
        r.pop("_id", None)
    return success_response(data=recruiters, message="Recruiters fetched successfully")

@router.post("/", response_model=APIResponse[dict])
async def create_recruiter(
    company_id: str,
    request: RecruiterCreateRequest,
    token: TokenPayload = Depends(require_own_company)
):
    user_repo = UserRepository()
    recruiter_repo = RecruiterRepository()
    
    # Check if user already exists
    existing_user = await user_repo.get_by_email(request.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="User with this email already exists")

    temp_password = generate_temp_password()
    hashed_pwd = hash_password(temp_password)

    # 1. Create User Document
    user_doc = {
        "email": request.email,
        "password_hash": hashed_pwd,
        "role": UserRole.RECRUITER.value,
        "company_id": company_id,
        "must_change_password": True,
        "is_active": True,
        "created_at": datetime.now(UTC),
        "updated_at": datetime.now(UTC),
    }
    user_id = await user_repo.create(user_doc)

    # 2. Create Recruiter Profile Document
    recruiter_doc = {
        "user_id": user_id,
        "company_id": company_id,
        "first_name": request.first_name,
        "last_name": request.last_name,
        "email": request.email,
        "phone": request.phone,
        "department": request.department,
        "designation": request.designation,
        "status": request.status,
        "created_at": datetime.now(UTC),
        "updated_at": datetime.now(UTC),
    }
    recruiter_id = await recruiter_repo.create(recruiter_doc)
    
    # Link recruiter_id back to user
    await user_repo.update(user_id, {"recruiter_id": recruiter_id})

    return success_response(
        data={
            "recruiter_id": recruiter_id,
            "username": request.email,
            "temporary_password": temp_password,
        },
        message="Recruiter created successfully"
    )

@router.get("/{recruiter_id}", response_model=APIResponse[dict])
async def get_recruiter(
    company_id: str,
    recruiter_id: str,
    token: TokenPayload = Depends(require_own_company)
):
    repo = RecruiterRepository()
    recruiter = await repo.get_by_id(recruiter_id)
    if not recruiter or str(recruiter.get("company_id")) != company_id:
        raise HTTPException(status_code=404, detail="Recruiter not found")
    
    recruiter["id"] = str(recruiter["_id"])
    recruiter.pop("_id", None)
    return success_response(data=recruiter)

@router.put("/{recruiter_id}", response_model=APIResponse[dict])
async def update_recruiter(
    company_id: str,
    recruiter_id: str,
    request: RecruiterUpdateRequest,
    token: TokenPayload = Depends(require_own_company)
):
    repo = RecruiterRepository()
    recruiter = await repo.get_by_id(recruiter_id)
    if not recruiter or str(recruiter.get("company_id")) != company_id:
        raise HTTPException(status_code=404, detail="Recruiter not found")
    
    update_data = {k: v for k, v in request.dict().items() if v is not None}
    update_data["updated_at"] = datetime.now(UTC)
    
    await repo.update(recruiter_id, update_data)
    
    # If status changed, update user status as well
    if "status" in update_data:
        user_repo = UserRepository()
        is_active = update_data["status"] == "active"
        if recruiter.get("user_id"):
            await user_repo.update(str(recruiter["user_id"]), {"is_active": is_active})

    return success_response(message="Recruiter updated successfully")

@router.delete("/{recruiter_id}", response_model=APIResponse[dict])
async def delete_recruiter(
    company_id: str,
    recruiter_id: str,
    token: TokenPayload = Depends(require_own_company)
):
    repo = RecruiterRepository()
    recruiter = await repo.get_by_id(recruiter_id)
    if not recruiter or str(recruiter.get("company_id")) != company_id:
        raise HTTPException(status_code=404, detail="Recruiter not found")
    
    await repo.delete(recruiter_id)
    
    if recruiter.get("user_id"):
        user_repo = UserRepository()
        await user_repo.delete(str(recruiter["user_id"]))
        
    return success_response(message="Recruiter deleted successfully")

@router.post("/{recruiter_id}/reset-password", response_model=APIResponse[dict])
async def reset_recruiter_password(
    company_id: str,
    recruiter_id: str,
    token: TokenPayload = Depends(require_own_company)
):
    repo = RecruiterRepository()
    recruiter = await repo.get_by_id(recruiter_id)
    if not recruiter or str(recruiter.get("company_id")) != company_id:
        raise HTTPException(status_code=404, detail="Recruiter not found")
        
    if not recruiter.get("user_id"):
        raise HTTPException(status_code=400, detail="Recruiter has no associated user account")
        
    temp_password = generate_temp_password()
    hashed_pwd = hash_password(temp_password)
    
    user_repo = UserRepository()
    await user_repo.update(str(recruiter["user_id"]), {
        "password_hash": hashed_pwd,
        "must_change_password": True
    })
    
    return success_response(
        data={
            "temporary_password": temp_password
        },
        message="Password reset successfully"
    )
