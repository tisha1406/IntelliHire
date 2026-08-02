from fastapi import APIRouter, HTTPException, status, Query, Depends
from typing import Optional

from app.repositories.company_repository import CompanyRepository
from app.services.company_service import CompanyService
from app.schemas.admin import (
    CompanyCreateRequest,
    CompanyCreateResponse,
    CompanyUpdateRequest,
    CompanyUpdateResponse,
    CompanyResponse
)
from app.schemas.response import APIResponse, success_response, error_response, PaginationMeta
from app.auth.jwt_handler import TokenPayload, decode_jwt
from app.rbac.permissions import require_role
from app.rbac.models import UserRole

router = APIRouter(
    prefix="/admin/companies",
    tags=["Admin - Companies"]
)


@router.get("", response_model=APIResponse[list[CompanyResponse]])
async def get_companies(
    limit: int = Query(10, ge=1),
    offset: int = Query(0, ge=0),
    search: str = Query(None, description="Search by name, email, or industry"),
    status_filter: str = Query(None, alias="status", description="Filter by status"),
    subscription: str = Query(None, description="Filter by subscription plan"),
    include_deleted: bool = Query(False, description="Include soft-deleted companies"),
    token: TokenPayload = Depends(require_role(UserRole.ADMIN))
):
    company_repo = CompanyRepository()

    query = {}
    if search:
        query["$or"] = [
            {"general.name": {"$regex": search, "$options": "i"}},
            {"general.contact_email": {"$regex": search, "$options": "i"}},
            {"general.industry": {"$regex": search, "$options": "i"}}
        ]
    if status_filter:
        query["subscription.status"] = status_filter
    if subscription:
        query["subscription.plan"] = subscription

    companies = await company_repo.get_many(
        query=query,
        limit=limit,
        skip=offset,
        include_deleted=include_deleted
    )
    
    total = await company_repo.count(query, include_deleted=include_deleted)

    response = []
    for company in companies:
        company["id"] = str(company["_id"])
        response.append(CompanyResponse(**company))

    pagination = PaginationMeta(
        total=total,
        limit=limit,
        skip=offset,
        has_more=(offset + limit) < total
    )

    return success_response(
        data=response,
        pagination=pagination,
        message="Companies retrieved successfully."
    )

@router.post("", response_model=APIResponse[CompanyCreateResponse], status_code=status.HTTP_201_CREATED)
async def create_company(
    request: CompanyCreateRequest,
    token: TokenPayload = Depends(require_role(UserRole.ADMIN))
):
    company_repo = CompanyRepository()
    existing = await company_repo.get_by_email(request.general.contact_email, include_deleted=True)

    if existing:
        raise HTTPException(status_code=409, detail="Company email already exists.")

    company_data = request.model_dump()
    
    service = CompanyService()
    company_id, username, temp_password = await service.create_company(company_data, created_by=token.sub)

    return success_response(
        data=CompanyCreateResponse(company_id=company_id, username=username, temporary_password=temp_password),
        message="Company created successfully."
    )

@router.get("/{company_id}", response_model=APIResponse[CompanyResponse])
async def get_company(
    company_id: str,
    token: TokenPayload = Depends(require_role(UserRole.ADMIN))
):
    company_repo = CompanyRepository()
    company = await company_repo.get_by_id(company_id, include_deleted=True)

    if not company:
        raise HTTPException(status_code=404, detail="Company not found.")

    company["id"] = str(company["_id"])
    return success_response(data=CompanyResponse(**company))


@router.patch("/{company_id}", response_model=APIResponse[CompanyUpdateResponse])
async def update_company(
    company_id: str,
    request: CompanyUpdateRequest,
    token: TokenPayload = Depends(require_role(UserRole.ADMIN))
):
    company_repo = CompanyRepository()
    company = await company_repo.get_by_id(company_id, include_deleted=False)

    if not company:
        raise HTTPException(status_code=404, detail="Company not found.")

    update_data = request.model_dump(exclude_none=True)

    if not update_data:
        raise HTTPException(status_code=400, detail="No fields provided for update.")

    service = CompanyService()
    await service.update_company(company_id, update_data, updated_by=token.sub)

    return success_response(
        data=CompanyUpdateResponse(updated_fields=list(update_data.keys())),
        message="Company updated successfully."
    )

@router.delete("/{company_id}", response_model=APIResponse[dict])
async def delete_company(
    company_id: str,
    token: TokenPayload = Depends(require_role(UserRole.ADMIN))
):
    company_repo = CompanyRepository()
    company = await company_repo.get_by_id(company_id, include_deleted=False)

    if not company:
        raise HTTPException(status_code=404, detail="Company not found.")

    service = CompanyService()
    await service.soft_delete(company_id, deleted_by=token.sub)

    return success_response(message="Company deleted successfully.")

@router.post("/{company_id}/restore", response_model=APIResponse[dict])
async def restore_company(
    company_id: str,
    token: TokenPayload = Depends(require_role(UserRole.ADMIN))
):
    company_repo = CompanyRepository()
    company = await company_repo.get_by_id(company_id, include_deleted=True)

    if not company:
        raise HTTPException(status_code=404, detail="Company not found.")

    if not company.get("deleted_at"):
        raise HTTPException(status_code=400, detail="Company is not deleted.")

    service = CompanyService()
    await service.restore_company(company_id, updated_by=token.sub)

    return success_response(message="Company restored successfully.")

@router.post("/{company_id}/suspend", response_model=APIResponse[dict])
async def suspend_company(
    company_id: str,
    token: TokenPayload = Depends(require_role(UserRole.ADMIN))
):
    company_repo = CompanyRepository()
    company = await company_repo.get_by_id(company_id, include_deleted=False)

    if not company:
        raise HTTPException(status_code=404, detail="Company not found.")

    service = CompanyService()
    await service.suspend_company(company_id, updated_by=token.sub)
    return success_response(message="Company suspended successfully.")

@router.post("/{company_id}/activate", response_model=APIResponse[dict])
async def activate_company(
    company_id: str,
    token: TokenPayload = Depends(require_role(UserRole.ADMIN))
):
    company_repo = CompanyRepository()
    company = await company_repo.get_by_id(company_id, include_deleted=False)

    if not company:
        raise HTTPException(status_code=404, detail="Company not found.")

    service = CompanyService()
    await service.activate_company(company_id, updated_by=token.sub)
    return success_response(message="Company activated successfully.")


@router.post("/{company_id}/reset-password", response_model=APIResponse[dict])
async def reset_password(
    company_id: str,
    token: TokenPayload = Depends(require_role(UserRole.ADMIN))
):
    company_repo = CompanyRepository()
    company = await company_repo.get_by_id(company_id, include_deleted=False)

    if not company:
        raise HTTPException(status_code=404, detail="Company not found.")

    service = CompanyService()
    temp_password = await service.reset_password(company_id, updated_by=token.sub)
    
    return success_response(
        data={"temporary_password": temp_password},
        message="Company password reset successfully."
    )