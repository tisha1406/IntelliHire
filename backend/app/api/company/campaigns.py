# pyrefly: ignore [missing-import]
from bson import ObjectId

from fastapi import APIRouter, HTTPException, Query, status, Depends
from app.auth.jwt_handler import TokenPayload
from app.rbac.models import UserRole
from app.rbac.permissions import require_role, require_company_or_recruiter

from app.repositories.campaign_repository import CampaignRepository

from app.schemas.company import (
    CampaignCreateRequest,
    CampaignUpdateRequest,
    CampaignResponse,
    CampaignUpdateResponse,
)

from pydantic import BaseModel

from app.middleware.limits import check_limit
from app.repositories.company_repository import CompanyRepository

router = APIRouter(
    prefix="/company/campaigns",
    tags=["Company - Campaigns"],
)

@router.post(
    "/",
    response_model=CampaignResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_campaign(
    request: CampaignCreateRequest,
    current_user: TokenPayload = Depends(require_role(UserRole.COMPANY)),
    _: TokenPayload = Depends(check_limit("max_campaigns", "campaigns_used")),
):
    repo = CampaignRepository()

    campaign = request.model_dump()

    # Discard any frontend-provided company_id
    campaign["company_id"] = ObjectId(
        current_user.sub
    )

    campaign["status"] = "active"

    campaign_id = await repo.create(
        campaign
    )

    company_repo = CompanyRepository()
    await company_repo.update_usage(current_user.sub, "campaigns_used", 1)

    # Log action
    from app.repositories.audit_log_repository import AuditLogRepository
    audit_repo = AuditLogRepository()
    await audit_repo.log_action(
        company_id=current_user.sub,
        actor_id=current_user.sub,
        actor_name=current_user.name,
        actor_role=current_user.role,
        action="CREATED_CAMPAIGN",
        target_entity="Campaign",
        target_id=str(campaign_id),
        target_name=request.name
    )

    return CampaignResponse(
        campaign_id=str(campaign_id)
    )

@router.get("/")
async def get_campaigns(
    limit: int = Query(10, ge=1),
    offset: int = Query(0, ge=0),
    current_user: TokenPayload = Depends(require_company_or_recruiter),
):
    repo = CampaignRepository()

    if current_user.role.upper() == UserRole.RECRUITER.value.upper():
        # Recruiter: return only assigned campaigns
        query = {
            "company_id": ObjectId(current_user.company_id),
            "assigned_recruiter_ids": ObjectId(current_user.recruiter_id),
        }
    else:
        # Company Admin: return all company campaigns
        query = {"company_id": ObjectId(current_user.sub)}

    campaigns = await repo.get_many(
        query=query,
        limit=limit,
        skip=offset,
    )

    for campaign in campaigns:
        campaign["_id"] = str(campaign["_id"])
        campaign["company_id"] = str(campaign["company_id"])
        if "assigned_recruiter_ids" in campaign:
            campaign["assigned_recruiter_ids"] = [str(r) for r in (campaign.get("assigned_recruiter_ids") or [])]

    return campaigns


class BulkAssignCampaignRequest(BaseModel):
    campaign_id: str
    recruiter_ids: list[str]


@router.post("/bulk-assign")
async def bulk_assign_campaign(
    req: BulkAssignCampaignRequest,
    current_user: TokenPayload = Depends(require_role(UserRole.COMPANY))
):
    repo = CampaignRepository()
    from app.repositories.recruiter_repository import RecruiterRepository
    recruiter_repo = RecruiterRepository()

    campaign = await repo.get_by_id(req.campaign_id)
    if not campaign or str(campaign.get("company_id")) != current_user.sub:
        raise HTTPException(status_code=404, detail="Campaign not found")

    # Validate all recruiters belong to the company
    valid_recruiter_ids = []
    for rid in req.recruiter_ids:
        rec = await recruiter_repo.get_by_id(rid)
        if rec and str(rec.get("company_id")) == current_user.sub and not rec.get("is_deleted"):
            valid_recruiter_ids.append(ObjectId(rid))

    # Add new recruiters to existing assigned recruiters, avoiding duplicates
    existing_rids = campaign.get("assigned_recruiter_ids", [])
    merged_rids = list(set([ObjectId(str(r)) for r in existing_rids] + valid_recruiter_ids))

    from datetime import datetime, UTC
    await repo.update(req.campaign_id, {
        "assigned_recruiter_ids": merged_rids,
        "updated_at": datetime.now(UTC),
        "updated_by": ObjectId(current_user.sub),
        "updated_by_role": current_user.role
    })
   
    # Log action
    from app.repositories.audit_log_repository import AuditLogRepository
    audit_repo = AuditLogRepository()
    await audit_repo.log_action(
        company_id=current_user.sub,
        actor_id=current_user.sub,
        actor_name=current_user.name,
        actor_role=current_user.role,
        action="ASSIGNED_CAMPAIGN",
        target_entity="Campaign",
        target_id=req.campaign_id,
        target_name=campaign.get("name"),
        metadata={"assigned_recruiters_count": len(valid_recruiter_ids)}
    )

    return {"message": f"Successfully assigned {len(valid_recruiter_ids)} recruiters to campaign.", "updated_count": len(valid_recruiter_ids)}


@router.get("/{campaign_id}")
async def get_campaign(
    campaign_id: str,
    current_user: TokenPayload = Depends(require_company_or_recruiter),
):
    repo = CampaignRepository()

    campaign = await repo.get_by_id(campaign_id)

    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found.")

    # Company: must own the campaign
    if current_user.role.upper() == UserRole.COMPANY.value.upper():
        if str(campaign.get("company_id")) != current_user.sub:
            raise HTTPException(status_code=404, detail="Campaign not found.")
    # Recruiter: must be assigned to the campaign AND belong to the company
    elif current_user.role.upper() == UserRole.RECRUITER.value.upper():
        if str(campaign.get("company_id")) != str(current_user.company_id):
            raise HTTPException(status_code=404, detail="Campaign not found.")
        if current_user.recruiter_id not in [str(r) for r in campaign.get("assigned_recruiter_ids", [])]:
            raise HTTPException(status_code=404, detail="Campaign not found.")

    campaign["_id"] = str(campaign["_id"])
    campaign["company_id"] = str(campaign["company_id"])

    return campaign


@router.patch(
    "/{campaign_id}",
    response_model=CampaignUpdateResponse,
)
async def update_campaign(
    campaign_id: str,
    request: CampaignUpdateRequest,
    current_user: TokenPayload = Depends(require_role(UserRole.COMPANY)),
):
    repo = CampaignRepository()

    campaign = await repo.get_by_id(
        campaign_id
    )

    if not campaign or str(campaign.get("company_id")) != current_user.sub:
        raise HTTPException(
            status_code=404,
            detail="Campaign not found.",
        )

    update_data = request.model_dump(
        exclude_none=True
    )

    if not update_data:
        raise HTTPException(
            status_code=400,
            detail="No fields provided.",
        )

    await repo.update(
        campaign_id,
        update_data,
    )

    return CampaignUpdateResponse(
        updated_fields=list(
            update_data.keys()
        )
    )

@router.delete("/{campaign_id}")
async def delete_campaign(
    campaign_id: str,
    current_user: TokenPayload = Depends(require_role(UserRole.COMPANY)),
):
    repo = CampaignRepository()

    campaign = await repo.get_by_id(
        campaign_id
    )

    if not campaign or str(campaign.get("company_id")) != current_user.sub:
        raise HTTPException(
            status_code=404,
            detail="Campaign not found.",
        )

    await repo.delete(
        campaign_id
    )

    company_repo = CompanyRepository()
    await company_repo.update_usage(current_user.sub, "campaigns_used", -1)

    return {
        "message": "Campaign deleted successfully."
    }
