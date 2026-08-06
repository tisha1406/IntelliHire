from bson import ObjectId

from fastapi import APIRouter, HTTPException, Query, status, Depends
from app.auth.jwt_handler import TokenPayload
from app.rbac.models import UserRole
from app.rbac.permissions import require_role

from app.repositories.campaign_repository import CampaignRepository

from app.schemas.company import (
    CampaignCreateRequest,
    CampaignUpdateRequest,
    CampaignResponse,
    CampaignUpdateResponse,
)

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

    return CampaignResponse(
        campaign_id=str(campaign_id)
    )

@router.get("/")
async def get_campaigns(
    limit: int = Query(10, ge=1),
    offset: int = Query(0, ge=0),
    current_user: TokenPayload = Depends(require_role(UserRole.COMPANY)),
):
    repo = CampaignRepository()

    campaigns = await repo.get_many(
        query={"company_id": ObjectId(current_user.sub)},
        limit=limit,
        skip=offset,
    )

    for campaign in campaigns:
        campaign["_id"] = str(
            campaign["_id"]
        )

        campaign["company_id"] = str(
            campaign["company_id"]
        )

    return campaigns

@router.get("/{campaign_id}")
async def get_campaign(
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

    campaign["_id"] = str(
        campaign["_id"]
    )

    campaign["company_id"] = str(
        campaign["company_id"]
    )

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