from fastapi import APIRouter, HTTPException, status, Query, Depends
from typing import Optional
from bson import ObjectId

from app.repositories.company_repository import CompanyRepository
from app.repositories.recruiter_repository import RecruiterRepository
from app.repositories.campaign_repository import CampaignRepository
from app.repositories.candidate_repository import CandidateRepository
from app.repositories.interview_session_repository import InterviewSessionRepository
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
from app.services.audit_service import AuditLogService, AuditLogCreate
from app.utils.relations import RelationResolver

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


@router.get("/{company_id}/stats", response_model=APIResponse[dict])
async def get_company_stats(
    company_id: str,
    token: TokenPayload = Depends(require_role(UserRole.ADMIN)),
):
    """
    Return live MongoDB statistics for a specific company.
    Used by Admin to monitor per-company activity in real time.
    """
    company_repo = CompanyRepository()
    recruiter_repo = RecruiterRepository()
    campaign_repo = CampaignRepository()
    candidate_repo = CandidateRepository()
    session_repo = InterviewSessionRepository()

    company = await company_repo.get_by_id(company_id, include_deleted=True)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found.")

    company_oid = ObjectId(company_id)

    # Live counts from their respective collections
    total_recruiters = await recruiter_repo.count({"company_id": company_id})
    active_recruiters = await recruiter_repo.count({"company_id": company_id, "status": "active"})
    total_campaigns = await campaign_repo.count({"company_id": company_oid})
    active_campaigns = await campaign_repo.count({"company_id": company_oid, "status": {"$in": ["active", "Active"]}})
    total_candidates = await candidate_repo.count({"company_id": company_oid})
    total_interviews = await session_repo.count({"company_id": company_oid})
    completed_interviews = await session_repo.count({"company_id": company_oid, "status": "completed"})

    success_rate = round((completed_interviews / total_interviews * 100), 1) if total_interviews > 0 else 0.0

    general = company.get("general", {})
    subscription = company.get("subscription", {})
    limits = company.get("limits", {})

    return success_response(
        data={
            "company_id": company_id,
            "company_name": company.get("company_name") or general.get("name", ""),
            "status": subscription.get("status") or company.get("status"),
            "subscription": subscription,
            "limits": limits,
            "last_login": str(company.get("last_login")) if company.get("last_login") else None,
            "created_at": str(company.get("created_at")) if company.get("created_at") else None,
            "usage": {
                "recruiters_used": total_recruiters,
                "active_recruiters": active_recruiters,
                "inactive_recruiters": total_recruiters - active_recruiters,
                "campaigns_used": total_campaigns,
                "active_campaigns": active_campaigns,
                "candidates_used": total_candidates,
                "interviews_conducted": total_interviews,
                "completed_interviews": completed_interviews,
                "interview_success_rate": success_rate,
            },
        },
        message="Company statistics retrieved successfully.",
    )

from app.schemas.admin import CompanySubscriptionSchema, CompanyLimitsSchema
from pydantic import BaseModel

class SubscriptionUpdateRequest(BaseModel):
    subscription: CompanySubscriptionSchema
    limits: CompanyLimitsSchema

class FeatureUpdateRequest(BaseModel):
    features: dict[str, bool]

@router.patch("/{company_id}/permissions", response_model=APIResponse[dict])
async def update_company_permissions(
    company_id: str,
    request: FeatureUpdateRequest,
    token: TokenPayload = Depends(require_role(UserRole.ADMIN)),
):
    company_repo = CompanyRepository()
    company = await company_repo.get_by_id(company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found.")

    await company_repo.update(company_id, {"features": request.features})
    
    await AuditLogService().log_action(AuditLogCreate(
        user_id=token.sub,
        action="update_company_permissions",
        entity_type="company",
        entity_id=company_id,
        details={"features_updated": request.features}
    ))
    
    return success_response(message="Permissions updated successfully.")

@router.patch("/{company_id}/subscription", response_model=APIResponse[dict])
async def update_company_subscription(
    company_id: str,
    request: SubscriptionUpdateRequest,
    token: TokenPayload = Depends(require_role(UserRole.ADMIN)),
):
    company_repo = CompanyRepository()
    company = await company_repo.get_by_id(company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found.")

    update_data = {
        "subscription": request.subscription.model_dump(),
        "limits": request.limits.model_dump()
    }
    await company_repo.update(company_id, update_data)
    
    await AuditLogService().log_action(AuditLogCreate(
        user_id=token.sub,
        action="update_company_subscription",
        entity_type="company",
        entity_id=company_id,
        details={"subscription": request.subscription.model_dump(), "limits": request.limits.model_dump()}
    ))
    
    return success_response(message="Subscription and limits updated successfully.")

@router.patch("/{company_id}/usage/reset", response_model=APIResponse[dict])
async def reset_company_usage(
    company_id: str,
    token: TokenPayload = Depends(require_role(UserRole.ADMIN)),
):
    company_repo = CompanyRepository()
    company = await company_repo.get_by_id(company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found.")

    await company_repo.update(company_id, {"usage": {}})
    return success_response(message="Usage counters reset successfully.")

@router.get("/{company_id}/recruiters", response_model=APIResponse[list[dict]])
async def get_company_recruiters(
    company_id: str,
    limit: int = Query(50, ge=1),
    offset: int = Query(0, ge=0),
    token: TokenPayload = Depends(require_role(UserRole.ADMIN)),
):
    recruiter_repo = RecruiterRepository()
    recruiters = await recruiter_repo.get_many(query={"company_id": company_id}, limit=limit, skip=offset)
    
    resolver = RelationResolver()
    recruiters = await resolver.populate(recruiters)
    
    for r in recruiters:
        r["id"] = str(r["_id"])
        if "_id" in r: del r["_id"]
    return success_response(data=recruiters, message="Recruiters retrieved successfully.")

@router.get("/{company_id}/campaigns", response_model=APIResponse[list[dict]])
async def get_company_campaigns(
    company_id: str,
    limit: int = Query(50, ge=1),
    offset: int = Query(0, ge=0),
    token: TokenPayload = Depends(require_role(UserRole.ADMIN)),
):
    campaign_repo = CampaignRepository()
    campaigns = await campaign_repo.get_many(query={"company_id": ObjectId(company_id)}, limit=limit, skip=offset)
    
    resolver = RelationResolver()
    campaigns = await resolver.populate(campaigns)
    
    for c in campaigns:
        c["id"] = str(c["_id"])
        c["company_id"] = str(c["company_id"])
        if "_id" in c: del c["_id"]
    return success_response(data=campaigns, message="Campaigns retrieved successfully.")

@router.get("/{company_id}/candidates", response_model=APIResponse[list[dict]])
async def get_company_candidates(
    company_id: str,
    limit: int = Query(50, ge=1),
    offset: int = Query(0, ge=0),
    token: TokenPayload = Depends(require_role(UserRole.ADMIN)),
):
    candidate_repo = CandidateRepository()
    candidates = await candidate_repo.get_many(query={"company_id": ObjectId(company_id)}, limit=limit, skip=offset)
    
    resolver = RelationResolver()
    candidates = await resolver.populate(candidates)
    
    for c in candidates:
        c["id"] = str(c["_id"])
        c["company_id"] = str(c["company_id"])
        if "_id" in c: del c["_id"]
    return success_response(data=candidates, message="Candidates retrieved successfully.")

@router.get("/{company_id}/interviews", response_model=APIResponse[list[dict]])
async def get_company_interviews(
    company_id: str,
    limit: int = Query(50, ge=1),
    offset: int = Query(0, ge=0),
    token: TokenPayload = Depends(require_role(UserRole.ADMIN)),
):
    from app.repositories.interview_session_repository import InterviewSessionRepository
    interview_repo = InterviewSessionRepository()
    interviews = await interview_repo.get_many(query={"company_id": ObjectId(company_id)}, limit=limit, skip=offset)
    
    resolver = RelationResolver()
    interviews = await resolver.populate(interviews)
    
    for i in interviews:
        i["id"] = str(i["_id"])
        i["company_id"] = str(i["company_id"])
        if "_id" in i: del i["_id"]
    return success_response(data=interviews, message="Interviews retrieved successfully.")

@router.get("/{company_id}/audit-logs", response_model=APIResponse[list[dict]])
async def get_company_audit_logs(
    company_id: str,
    limit: int = Query(50, ge=1),
    offset: int = Query(0, ge=0),
    token: TokenPayload = Depends(require_role(UserRole.ADMIN)),
):
    logs = await AuditLogService().get_company_logs(company_id=company_id, limit=limit, skip=offset)
    for log in logs:
        log["id"] = str(log["_id"])
        del log["_id"]
    return success_response(data=logs, message="Audit logs retrieved successfully.")