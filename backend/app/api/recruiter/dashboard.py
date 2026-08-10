from fastapi import APIRouter, Depends
from typing import Dict, Any

from app.auth.jwt_handler import TokenPayload
from app.rbac.permissions import require_recruiter_scope
from app.schemas.response import APIResponse, success_response
from app.repositories.candidate_repository import CandidateRepository
from app.repositories.campaign_repository import CampaignRepository
from app.repositories.interview_session_repository import InterviewSessionRepository
from app.repositories.audit_log_repository import AuditLogRepository
from datetime import datetime, timezone, timedelta
from bson import ObjectId

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
    candidates = await candidate_repo.get_many({"assigned_recruiter_id": ObjectId(recruiter_id)})
    total_candidates = len(candidates)
    
    invited_candidates = len([c for c in candidates if c.get("status") == "INVITED"])
    shortlisted_candidates = len([c for c in candidates if c.get("status") == "SHORTLISTED"])
    
    # Campaigns assigned
    campaigns = await campaign_repo.get_many({"assigned_recruiter_ids": ObjectId(recruiter_id)})
    total_campaigns = len(campaigns)
    
    # Interview sessions
    candidate_ids = [str(c["_id"]) for c in candidates]
    interviews = []
    if candidate_ids:
        interviews = await interview_repo.get_many({"candidate_id": {"$in": candidate_ids}})
        
    scheduled_interviews = len([i for i in interviews if i.get("status") == "scheduled"])
    completed_interviews = len([i for i in interviews if i.get("status") == "completed"])
    
    start_of_day = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_day = start_of_day + timedelta(days=1)
    todays_interviews = 0
    for i in interviews:
        sch = i.get("scheduled_at")
        if sch and isinstance(sch, datetime) and start_of_day <= sch < end_of_day:
            todays_interviews += 1
    
    # Calculate some averages
    # Assuming candidate docs have 'resume_score' and interviews have 'overall_score'
    resume_scores = [c.get("resume_score", 0) for c in candidates if c.get("resume_score")]
    avg_resume_score = sum(resume_scores) / len(resume_scores) if resume_scores else 0
    
    interview_scores = [i.get("overall_score", 0) for i in interviews if i.get("overall_score")]
    avg_interview_score = sum(interview_scores) / len(interview_scores) if interview_scores else 0
    
    acceptance_rate = (completed_interviews / invited_candidates * 100) if invited_candidates > 0 else 0
    
    # Recent Activity
    audit_repo = AuditLogRepository()
    raw_logs = await audit_repo.get_by_actor(token.company_id, recruiter_id, limit=10)
    recent_activity = []
    for log in raw_logs:
        log["id"] = str(log["_id"])
        log.pop("_id", None)
        log["actor_id"] = str(log["actor_id"])
        log["company_id"] = str(log["company_id"])
        recent_activity.append(log)
    
    stats = {
        "candidatesAssigned": total_candidates,
        "candidatesAdded": total_candidates, # Simplification: assuming assigned == added for recruiter dashboard
        "candidatesInvited": invited_candidates,
        "candidatesShortlisted": shortlisted_candidates,
        "campaignsAssigned": total_campaigns,
        "interviewsScheduled": scheduled_interviews,
        "completedInterviews": completed_interviews,
        "todaysInterviews": todays_interviews,
        "pendingInvitations": invited_candidates - scheduled_interviews,
        "acceptanceRate": round(acceptance_rate, 1),
        "averageResumeScore": round(avg_resume_score, 1),
        "averageInterviewScore": round(avg_interview_score, 1),
        "recentActivity": recent_activity
    }
    
    return success_response(data=stats)
