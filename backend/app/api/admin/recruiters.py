from fastapi import APIRouter, HTTPException, Query, Depends, status
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timezone

from app.repositories.recruiter_repository import RecruiterRepository
from app.repositories.company_repository import CompanyRepository
from app.schemas.response import APIResponse, success_response, PaginationMeta
from app.auth.jwt_handler import TokenPayload, decode_jwt
from app.rbac.permissions import require_role
from app.rbac.models import UserRole

router = APIRouter(
    prefix="/admin/recruiters",
    tags=["Admin - Recruiters"]
)

class RecruiterCreateRequest(BaseModel):
    name: str
    email: str
    company_id: str
    role: str = "recruiter"

class RecruiterUpdateRequest(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None
    company_id: Optional[str] = None

@router.get("/", response_model=APIResponse[list[dict]])
async def get_recruiters(
    limit: int = Query(10, ge=1),
    offset: int = Query(0, ge=0),
    search: Optional[str] = Query(None, description="Search by name or email"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status"),
    company_id: Optional[str] = Query(None, description="Filter by company"),
    token: TokenPayload = Depends(require_role(UserRole.ADMIN))
):
    repo = RecruiterRepository()

    query = {}
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"email": {"$regex": search, "$options": "i"}}
        ]
    if status_filter:
        query["status"] = status_filter
    if company_id:
        query["company_id"] = company_id

    recruiters = await repo.get_many(query=query, limit=limit, skip=offset)
    total = await repo.count(query)

    for rec in recruiters:
        rec["id"] = str(rec["_id"])
        del rec["_id"]

    pagination = PaginationMeta(
        total=total,
        limit=limit,
        skip=offset,
        has_more=(offset + limit) < total
    )

    return success_response(
        data=recruiters,
        pagination=pagination,
        message="Recruiters retrieved successfully."
    )

@router.post("/", response_model=APIResponse[dict], status_code=status.HTTP_201_CREATED)
async def create_recruiter(
    request: RecruiterCreateRequest,
    token: TokenPayload = Depends(require_role(UserRole.ADMIN))
):
    repo = RecruiterRepository()
    company_repo = CompanyRepository()

    existing = await repo.get_by_email(request.email)
    if existing:
        raise HTTPException(status_code=409, detail="Recruiter email already exists.")

    company = await company_repo.get_by_id(request.company_id)
    if not company:
        raise HTTPException(status_code=400, detail="Invalid company ID.")

    recruiter = {
        "name": request.name,
        "email": request.email,
        "company_id": request.company_id,
        "company_name": company.get("general", {}).get("name"),
        "role": request.role,
        "status": "active",
        "created_at": datetime.now(timezone.utc).isoformat()
    }

    recruiter_id = await repo.create(recruiter)

    return success_response(
        data={"recruiter_id": recruiter_id},
        message="Recruiter created successfully."
    )

@router.get("/{recruiter_id}", response_model=APIResponse[dict])
async def get_recruiter(
    recruiter_id: str,
    token: TokenPayload = Depends(require_role(UserRole.ADMIN))
):
    repo = RecruiterRepository()
    rec = await repo.get_by_id(recruiter_id)

    if not rec:
        raise HTTPException(status_code=404, detail="Recruiter not found.")

    rec["id"] = str(rec["_id"])
    del rec["_id"]

    return success_response(data=rec)

@router.patch("/{recruiter_id}", response_model=APIResponse[dict])
async def update_recruiter(
    recruiter_id: str,
    request: RecruiterUpdateRequest,
    token: TokenPayload = Depends(require_role(UserRole.ADMIN))
):
    repo = RecruiterRepository()
    rec = await repo.get_by_id(recruiter_id)

    if not rec:
        raise HTTPException(status_code=404, detail="Recruiter not found.")

    update_data = request.model_dump(exclude_none=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields provided for update.")

    if update_data.get("company_id"):
        company_repo = CompanyRepository()
        company = await company_repo.get_by_id(update_data["company_id"])
        if not company:
            raise HTTPException(status_code=400, detail="Invalid company ID.")
        update_data["company_name"] = company.get("general", {}).get("name")

    await repo.update(recruiter_id, update_data)
    
    from app.services.audit_service import AuditLogService, AuditLogCreate
    await AuditLogService().log_action(AuditLogCreate(
        user_id=token.sub,
        action="update_recruiter",
        entity_type="recruiter",
        entity_id=recruiter_id,
        details={"fields_updated": list(update_data.keys())}
    ))

    return success_response(
        data={"updated_fields": list(update_data.keys())},
        message="Recruiter updated successfully."
    )

@router.delete("/{recruiter_id}", response_model=APIResponse[dict])
async def delete_recruiter(
    recruiter_id: str,
    token: TokenPayload = Depends(require_role(UserRole.ADMIN))
):
    repo = RecruiterRepository()
    rec = await repo.get_by_id(recruiter_id)

    if not rec:
        raise HTTPException(status_code=404, detail="Recruiter not found.")

    await repo.delete(recruiter_id)
    
    from app.services.audit_service import AuditLogService, AuditLogCreate
    await AuditLogService().log_action(AuditLogCreate(
        user_id=token.sub,
        action="delete_recruiter",
        entity_type="recruiter",
        entity_id=recruiter_id
    ))

    return success_response(message="Recruiter deleted successfully.")

@router.post("/{recruiter_id}/suspend", response_model=APIResponse[dict])
async def suspend_recruiter(
    recruiter_id: str,
    token: TokenPayload = Depends(require_role(UserRole.ADMIN))
):
    repo = RecruiterRepository()
    rec = await repo.get_by_id(recruiter_id)

    if not rec:
        raise HTTPException(status_code=404, detail="Recruiter not found.")

    await repo.update(recruiter_id, {"status": "suspended"})
    
    from app.services.audit_service import AuditLogService, AuditLogCreate
    await AuditLogService().log_action(AuditLogCreate(
        user_id=token.sub,
        action="suspend_recruiter",
        entity_type="recruiter",
        entity_id=recruiter_id
    ))
    
    return success_response(message="Recruiter suspended successfully.")

@router.post("/{recruiter_id}/activate", response_model=APIResponse[dict])
async def activate_recruiter(
    recruiter_id: str,
    token: TokenPayload = Depends(require_role(UserRole.ADMIN))
):
    repo = RecruiterRepository()
    rec = await repo.get_by_id(recruiter_id)

    if not rec:
        raise HTTPException(status_code=404, detail="Recruiter not found.")

    await repo.update(recruiter_id, {"status": "active"})
    
    from app.services.audit_service import AuditLogService, AuditLogCreate
    await AuditLogService().log_action(AuditLogCreate(
        user_id=token.sub,
        action="activate_recruiter",
        entity_type="recruiter",
        entity_id=recruiter_id
    ))
    
    return success_response(message="Recruiter activated successfully.")
