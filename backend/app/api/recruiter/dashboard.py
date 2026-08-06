from fastapi import APIRouter, Depends
from typing import Dict, Any

from app.auth.jwt_handler import TokenPayload
from app.rbac.permissions import require_recruiter_scope
from app.schemas.response import APIResponse, success_response
from app.repositories.candidate_repository import CandidateRepository
from app.repositories.campaign_repository import CampaignRepository
from app.repositories.interview_session_repository import InterviewSessionRepository

router = APIRouter(
    prefix="/dashboard",
    tags=["Recruiter - Dashboard"]
)

@router.get("/stats", response_model=APIResponse[Dict[str, Any]])
async def get_dashboard_stats(
    token: TokenPayload = Depends(require_recruiter_scope)
):
    recruiter_id = token.recruiter_id
    
    candidate_repo = CandidateRepository()
    campaign_repo = CampaignRepository()
    interview_repo = InterviewSessionRepository()
    
    # Candidates assigned
    candidates = await candidate_repo.get_many({"assigned_recruiter_id": recruiter_id})
    total_candidates = len(candidates)
    
    invited_candidates = len([c for c in candidates if c.get("status") == "INVITED"])
    shortlisted_candidates = len([c for c in candidates if c.get("status") == "SHORTLISTED"])
    
    # Campaigns assigned
    campaigns = await campaign_repo.get_many({"assigned_recruiter_ids": recruiter_id})
    total_campaigns = len(campaigns)
    
    # Interview sessions
    candidate_ids = [str(c["_id"]) for c in candidates]
    interviews = []
    if candidate_ids:
        interviews = await interview_repo.get_many({"candidate_id": {"$in": candidate_ids}})
        
    scheduled_interviews = len([i for i in interviews if i.get("status") == "scheduled"])
    completed_interviews = len([i for i in interviews if i.get("status") == "completed"])
    
    # Calculate some averages
    # Assuming candidate docs have 'resume_score' and interviews have 'overall_score'
    resume_scores = [c.get("resume_score", 0) for c in candidates if c.get("resume_score")]
    avg_resume_score = sum(resume_scores) / len(resume_scores) if resume_scores else 0
    
    interview_scores = [i.get("overall_score", 0) for i in interviews if i.get("overall_score")]
    avg_interview_score = sum(interview_scores) / len(interview_scores) if interview_scores else 0
    
    acceptance_rate = (completed_interviews / invited_candidates * 100) if invited_candidates > 0 else 0
    
    stats = {
        "candidatesAssigned": total_candidates,
        "candidatesInvited": invited_candidates,
        "candidatesShortlisted": shortlisted_candidates,
        "campaignsAssigned": total_campaigns,
        "interviewsScheduled": scheduled_interviews,
        "completedInterviews": completed_interviews,
        "pendingInvitations": invited_candidates - scheduled_interviews,
        "acceptanceRate": round(acceptance_rate, 1),
        "averageResumeScore": round(avg_resume_score, 1),
        "averageInterviewScore": round(avg_interview_score, 1)
    }
    
    return success_response(data=stats)
