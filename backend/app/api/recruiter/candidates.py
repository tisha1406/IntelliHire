from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime, UTC

from app.auth.jwt_handler import TokenPayload
from app.rbac.permissions import require_recruiter_scope
from app.schemas.response import APIResponse, success_response
from app.repositories.candidate_repository import CandidateRepository
from app.repositories.campaign_repository import CampaignRepository

router = APIRouter(
    prefix="/candidates",
    tags=["Recruiter - Candidates"]
)

class CandidateCreateRequest(BaseModel):
    name: str
    email: str
    phone: str
    campaign_id: str
    interview_type: str
    resume_id: Optional[str] = None

@router.get("/", response_model=APIResponse[list])
async def get_recruiter_candidates(
    token: TokenPayload = Depends(require_recruiter_scope)
):
    repo = CandidateRepository()
    candidates = await repo.get_many({"assigned_recruiter_id": token.recruiter_id})
    for c in candidates:
        c["id"] = str(c["_id"])
        c.pop("_id", None)
    return success_response(data=candidates)

@router.post("/", response_model=APIResponse[dict])
async def create_candidate(
    request: CandidateCreateRequest,
    token: TokenPayload = Depends(require_recruiter_scope)
):
    # Verify campaign is assigned to recruiter
    camp_repo = CampaignRepository()
    campaign = await camp_repo.get_by_id(request.campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
        
    if token.recruiter_id not in [str(r) for r in campaign.get("assigned_recruiter_ids", [])]:
        raise HTTPException(status_code=403, detail="You are not assigned to this campaign")
        
    repo = CandidateRepository()
    
    candidate_doc = {
        "company_id": token.company_id,
        "campaign_id": request.campaign_id,
        "assigned_recruiter_id": token.recruiter_id,
        "name": request.name,
        "email": request.email,
        "phone": request.phone,
        "interview_type": request.interview_type,
        "resume_id": request.resume_id,
        "status": "INVITED",
        "current_stage": "Invited",
        "created_at": datetime.now(UTC),
        "updated_at": datetime.now(UTC)
    }
    
    candidate_id = await repo.create(candidate_doc)
    
    # Normally we would generate credentials and send invite email here
    # Placeholder for credentials generation logic
    
    return success_response(
        data={"candidate_id": candidate_id},
        message="Candidate created and invited successfully"
    )

@router.patch("/{candidate_id}/shortlist", response_model=APIResponse[dict])
async def shortlist_candidate(
    candidate_id: str,
    token: TokenPayload = Depends(require_recruiter_scope)
):
    repo = CandidateRepository()
    candidate = await repo.get_by_id(candidate_id)
    if not candidate or str(candidate.get("assigned_recruiter_id")) != token.recruiter_id:
        raise HTTPException(status_code=404, detail="Candidate not found in your assigned list")
        
    await repo.update(candidate_id, {
        "status": "SHORTLISTED",
        "current_stage": "Shortlisted",
        "updated_at": datetime.now(UTC)
    })
    return success_response(message="Candidate shortlisted")

@router.patch("/{candidate_id}/reject", response_model=APIResponse[dict])
async def reject_candidate(
    candidate_id: str,
    token: TokenPayload = Depends(require_recruiter_scope)
):
    repo = CandidateRepository()
    candidate = await repo.get_by_id(candidate_id)
    if not candidate or str(candidate.get("assigned_recruiter_id")) != token.recruiter_id:
        raise HTTPException(status_code=404, detail="Candidate not found in your assigned list")
        
    await repo.update(candidate_id, {
        "status": "REJECTED",
        "current_stage": "Rejected",
        "updated_at": datetime.now(UTC)
    })
    return success_response(message="Candidate rejected")

@router.post("/{candidate_id}/send-invite", response_model=APIResponse[dict])
async def send_invite(
    candidate_id: str,
    token: TokenPayload = Depends(require_recruiter_scope)
):
    repo = CandidateRepository()
    candidate = await repo.get_by_id(candidate_id)
    if not candidate or str(candidate.get("assigned_recruiter_id")) != token.recruiter_id:
        raise HTTPException(status_code=404, detail="Candidate not found in your assigned list")
        
    # Trigger invite email logic here
    
    await repo.update(candidate_id, {
        "status": "INVITED",
        "current_stage": "Invited",
        "updated_at": datetime.now(UTC)
    })
    return success_response(message="Interview invitation sent successfully")
