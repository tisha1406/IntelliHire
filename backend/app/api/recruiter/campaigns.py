from fastapi import APIRouter, Depends, HTTPException
from typing import List

from app.auth.jwt_handler import TokenPayload
from app.rbac.permissions import require_recruiter_scope
from app.schemas.response import APIResponse, success_response
from app.repositories.campaign_repository import CampaignRepository

router = APIRouter(
    prefix="/campaigns",
    tags=["Recruiter - Campaigns"]
)

@router.get("/", response_model=APIResponse[list])
async def get_recruiter_campaigns(
    token: TokenPayload = Depends(require_recruiter_scope)
):
    repo = CampaignRepository()
    campaigns = await repo.get_many({"assigned_recruiter_ids": token.recruiter_id})
    for c in campaigns:
        c["id"] = str(c["_id"])
        c.pop("_id", None)
    return success_response(data=campaigns)

@router.get("/{campaign_id}", response_model=APIResponse[dict])
async def get_recruiter_campaign(
    campaign_id: str,
    token: TokenPayload = Depends(require_recruiter_scope)
):
    repo = CampaignRepository()
    campaign = await repo.get_by_id(campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
        
    if token.recruiter_id not in [str(r) for r in campaign.get("assigned_recruiter_ids", [])]:
        raise HTTPException(status_code=403, detail="You are not assigned to this campaign")
        
    campaign["id"] = str(campaign["_id"])
    campaign.pop("_id", None)
    return success_response(data=campaign)
