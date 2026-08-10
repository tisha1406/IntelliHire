"""
Company Dashboard API
Aggregates all company-specific stats into a single endpoint.
Every value is computed dynamically from MongoDB — no mocks.
"""
from datetime import datetime, timezone
from bson import ObjectId
from fastapi import APIRouter, Depends

from app.auth.jwt_handler import TokenPayload
from app.rbac.models import UserRole
from app.rbac.permissions import require_company_or_recruiter
from app.schemas.response import APIResponse, success_response

from app.repositories.company_repository import CompanyRepository
from app.repositories.campaign_repository import CampaignRepository
from app.repositories.candidate_repository import CandidateRepository
from app.repositories.recruiter_repository import RecruiterRepository
from app.repositories.interview_session_repository import InterviewSessionRepository
from app.repositories.company_notification_repository import CompanyNotificationRepository
from app.db.mongo import serialize_mongo_doc

router = APIRouter(
    prefix="/company/dashboard",
    tags=["Company - Dashboard"],
)


@router.get("", response_model=APIResponse[dict])
async def get_company_dashboard(
    current_user: TokenPayload = Depends(require_company_or_recruiter),
):
    """
    Aggregated company dashboard.
    Returns all data the frontend dashboard needs in one call.
    - Company Admin: scoped by sub (their own company)
    - Recruiter: scoped by company_id from JWT (the company they belong to)
    """
    # Resolve company_id based on role
    if current_user.role.upper() == UserRole.RECRUITER.value.upper():
        company_id_str = current_user.company_id
    else:
        company_id_str = current_user.sub

    if not company_id_str:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="company_id not found in token.")

    company_oid = ObjectId(company_id_str)
    
    company_filter = {"company_id": company_oid}
    campaign_filter = {"company_id": company_oid}
    candidate_filter = {"company_id": company_oid}
    
    if current_user.role.upper() == UserRole.RECRUITER.value.upper():
        campaign_filter["assigned_recruiter_ids"] = ObjectId(current_user.recruiter_id)
        candidate_filter["assigned_recruiter_id"] = ObjectId(current_user.recruiter_id)

    # ── Repositories ──────────────────────────────────────────────────
    company_repo = CompanyRepository()
    campaign_repo = CampaignRepository()
    candidate_repo = CandidateRepository()
    recruiter_repo = RecruiterRepository()
    session_repo = InterviewSessionRepository()
    notif_repo = CompanyNotificationRepository()

    # ── 1. Company profile ────────────────────────────────────────────
    company = await company_repo.get_by_id(company_id_str)
    general = company.get("general", {}) if company else {}
    subscription = company.get("subscription", {}) if company else {}
    limits = company.get("limits", {}) if company else {}

    profile = {
        "company_name": company.get("company_name") or general.get("name", ""),
        "logo": general.get("logo_url") or company.get("logo"),
        "industry": general.get("industry"),
        "contact_email": general.get("contact_email"),
        "contact_person": general.get("contact_person"),
        "phone": general.get("phone"),
        "website": general.get("website"),
        "subscription": subscription,
        "status": company.get("status"),
        "last_login": company.get("last_login"),
    }

    # ── 2. Live usage counts (dynamic — no stored counters yet) ───────
    total_recruiters = await recruiter_repo.count({"company_id": company_id_str})
    total_campaigns = await campaign_repo.count(campaign_filter)
    total_candidates = await candidate_repo.count(candidate_filter)
    
    # For interviews, we need to query by candidate_ids
    if current_user.role.upper() == UserRole.RECRUITER.value.upper():
        candidate_docs = await candidate_repo.get_many(candidate_filter)
        candidate_ids = [c["_id"] for c in candidate_docs]
        interview_filter = {"company_id": company_oid, "candidate_id": {"$in": candidate_ids}}
    else:
        interview_filter = {"company_id": company_oid}
        
    total_interviews = await session_repo.count(interview_filter)
    completed_interviews = await session_repo.count({**interview_filter, "status": "completed"})
    active_campaigns = await campaign_repo.count({**campaign_filter, "status": "active"})
    hired_candidates = await candidate_repo.count({**candidate_filter, "status": {"$in": ["hired", "Hired", "Selected"]}})

    usage = {
        "recruiters_used": total_recruiters,
        "campaigns_used": total_campaigns,
        "candidates_used": total_candidates,
        "interviews_conducted": total_interviews,
        "completed_interviews": completed_interviews,
        "active_campaigns": active_campaigns,
        "hired_candidates": hired_candidates,
    }

    # ── 3. KPI summary cards ──────────────────────────────────────────
    success_rate = round((completed_interviews / total_interviews * 100), 1) if total_interviews > 0 else 0.0

    kpis = {
        "totalApplications": {"value": str(total_candidates), "positive": True},
        "totalInterviews": {"value": str(total_interviews), "positive": True},
        "activeCampaigns": {"value": str(active_campaigns), "positive": True},
        "hiredCandidates": {"value": str(hired_candidates), "positive": True},
        "successRate": {"value": f"{success_rate}%", "positive": True},
        "totalRecruiters": {"value": str(total_recruiters), "positive": True},
    }

    # ── 4. Recent campaigns (last 5) ─────────────────────────────────
    raw_campaigns = await campaign_repo.get_many(
        query=campaign_filter,
        limit=5,
    )
    recent_campaigns = []
    for c in raw_campaigns:
        recent_campaigns.append({
            "id": str(c["_id"]),
            "title": c.get("title") or c.get("name", "Untitled"),
            "status": c.get("status", ""),
            "candidates": c.get("candidate_count", 0),
            "created_at": c.get("created_at"),
        })

    # ── 5. Recent candidates (last 5) ────────────────────────────────
    raw_candidates_cursor = (
        candidate_repo.collection
        .find(candidate_filter)
        .sort("created_at", -1)
        .limit(5)
    )
    raw_candidates = await raw_candidates_cursor.to_list(length=5)
    recent_candidates = []
    for c in raw_candidates:
        recent_candidates.append({
            "id": str(c["_id"]),
            "name": c.get("name", ""),
            "email": c.get("email", ""),
            "status": c.get("status", ""),
            "campaign_id": str(c.get("campaign_id", "")),
            "created_at": c.get("created_at"),
        })

    # ── 6. Recent interviews (last 5) ────────────────────────────────
    raw_interviews_cursor = (
        session_repo.collection
        .find(interview_filter)
        .sort("created_at", -1)
        .limit(5)
    )
    raw_interviews = await raw_interviews_cursor.to_list(length=5)
    recent_interviews = []
    for s in raw_interviews:
        recent_interviews.append({
            "id": str(s["_id"]),
            "candidate_id": str(s.get("candidate_id", "")),
            "status": s.get("status", ""),
            "overall_score": s.get("overall_score"),
            "created_at": s.get("created_at"),
        })

    # ── 7. Recent notifications (last 5) ─────────────────────────────
    raw_notifs = await notif_repo.get_for_company(company_id_str, limit=5)
    recent_notifications = []
    for n in raw_notifs:
        recent_notifications.append({
            "id": str(n["_id"]),
            "type": n.get("type", "info"),
            "title": n.get("title", ""),
            "message": n.get("message", ""),
            "is_read": n.get("is_read", False),
            "created_at": n.get("created_at"),
        })

    unread_notifications = await notif_repo.get_unread_count(company_id_str)

    # ── 8. Monthly hiring trend (last 6 months from candidates) ───────
    from datetime import timedelta
    today = datetime.now(timezone.utc)
    hiring_trend = []
    month_labels = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

    for i in range(5, -1, -1):
        # Approximate month start/end
        target_date = today - timedelta(days=30 * i)
        month_idx = target_date.month - 1
        year = target_date.year
        
        base_date_query = {
            "created_at": {
                "$gte": datetime(year, target_date.month, 1),
                "$lt": (
                    datetime(year + 1, 1, 1) if target_date.month == 12
                    else datetime(year, target_date.month + 1, 1)
                ),
            }
        }

        apps = await candidate_repo.collection.count_documents({**candidate_filter, **base_date_query})
        selected = await candidate_repo.collection.count_documents({
            **candidate_filter,
            **base_date_query,
            "status": {"$in": ["hired", "Hired", "Selected"]}
        })
        hiring_trend.append({
            "month": month_labels[month_idx],
            "applications": apps,
            "selections": selected,
        })

    # ── 9. Hiring funnel ──────────────────────────────────────────────
    STATUS_STAGES = [
        ("Applied", ["applied", "Applied", "New", "new"]),
        ("AI Screened", ["screened", "Screened", "shortlisted", "Shortlisted"]),
        ("Interview", ["interview_scheduled", "Interviewed", "in_progress"]),
        ("Offered", ["offered", "Offered"]),
        ("Hired", ["hired", "Hired", "Selected", "selected"]),
    ]

    funnel_total = total_candidates or 1
    hiring_funnel = []
    for stage_label, statuses in STATUS_STAGES:
        count = await candidate_repo.count({
            **candidate_filter,
            "status": {"$in": statuses},
        })
        pct = round((count / funnel_total) * 100, 1)
        hiring_funnel.append({
            "stage": stage_label,
            "count": count,
            "percentage": min(pct, 100),
        })

    # ── 10. Recruiter Workload ────────────────────────────────────────
    recruiters = await recruiter_repo.get_many(company_filter)
    recruiter_workload = []
    
    # Pre-fetch all candidates and sessions to avoid N+1 queries if possible
    # For now, simple aggregation per recruiter
    for rec in recruiters:
        rec_id = ObjectId(rec["_id"])
        r_candidates = await candidate_repo.count({"company_id": company_oid, "assigned_recruiter_id": rec_id})
        r_campaigns = await campaign_repo.count({"company_id": company_oid, "assigned_recruiter_ids": rec_id})
        
        # Today's interviews
        start_of_day = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day + timedelta(days=1)
        
        r_sessions = await session_repo.get_many({
            "company_id": company_oid,
        })
        # Find candidates for this recruiter
        all_cands = await candidate_repo.get_many({"company_id": company_oid, "assigned_recruiter_id": rec_id})
        invited = len([c for c in all_cands if c.get("status", "").lower() in ["invited", "pending"]])
        evaluating = len([c for c in all_cands if c.get("status", "").lower() in ["evaluating", "interviewing", "interviewed"]])
        shortlisted = len([c for c in all_cands if c.get("status", "").lower() == "shortlisted"])
        hired = len([c for c in all_cands if c.get("status", "").lower() in ["hired", "selected"]])
        rejected = len([c for c in all_cands if c.get("status", "").lower() == "rejected"])

        r_candidate_ids = [c["_id"] for c in all_cands]
        
        todays_interviews = 0
        scores = []
        for s in r_sessions:
            if s.get("candidate_id") in r_candidate_ids:
                if s.get("overall_score") is not None:
                    scores.append(s.get("overall_score"))
                
                # check if scheduled today
                sch = s.get("scheduled_at")
                if sch and isinstance(sch, datetime) and start_of_day <= sch < end_of_day:
                    todays_interviews += 1
                    
        r_avg_score = round(sum(scores) / len(scores), 1) if scores else 0.0
        
        recruiter_workload.append({
            "id": str(rec["_id"]),
            "name": rec.get("name", f"{rec.get('first_name', '')} {rec.get('last_name', '')}".strip()),
            "status": rec.get("status", rec.get("account_status", "active")),
            "candidates_count": r_candidates,
            "campaigns_count": r_campaigns,
            "interviews_today": todays_interviews,
            "avg_score": r_avg_score
        })

    # ── Assemble response ─────────────────────────────────────────────
    return success_response(
        data={
            "profile": profile,
            "subscription": subscription,
            "limits": limits,
            "usage": usage,
            "kpis": kpis,
            "recent_campaigns": recent_campaigns,
            "recent_candidates": recent_candidates,
            "recent_interviews": recent_interviews,
            "recent_notifications": recent_notifications,
            "unread_notifications": unread_notifications,
            "hiring_trend": hiring_trend,
            "hiring_funnel": hiring_funnel,
            "recruiter_workload": recruiter_workload,
        },
        message="Dashboard data retrieved successfully.",
    )
