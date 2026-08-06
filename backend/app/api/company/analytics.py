"""
Company Analytics API
All analytics are computed from real MongoDB data scoped to the authenticated company.
No fallback/mock data — when the DB is empty, endpoints return empty arrays/zeros.
"""
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Optional

from fastapi import APIRouter, Query, Depends
from bson import ObjectId

from app.auth.jwt_handler import TokenPayload
from app.rbac.models import UserRole
from app.rbac.permissions import require_role
from app.middleware.feature_guard import require_feature

from app.repositories.candidate_repository import CandidateRepository
from app.repositories.job_repository import JobRepository
from app.repositories.campaign_repository import CampaignRepository
from app.repositories.interview_session_repository import InterviewSessionRepository

router = APIRouter(
    prefix="/company/analytics", 
    tags=["Company Analytics"],
    dependencies=[Depends(require_feature("analytics"))]
)

candidate_repo = CandidateRepository()
job_repo = JobRepository()
campaign_repo = CampaignRepository()
session_repo = InterviewSessionRepository()

MONTH_LABELS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


# ──────────────────────────────────────────────────────────────────────
# GET /company/analytics/kpis
# ──────────────────────────────────────────────────────────────────────

@router.get("/kpis", summary="Get Live KPI Metrics")
async def get_kpis(
    current_user: TokenPayload = Depends(require_role(UserRole.COMPANY)),
):
    """Return real-time KPI metrics from MongoDB. Returns zeros when data is empty."""
    company_oid = ObjectId(current_user.sub)
    company_filter = {"company_id": company_oid}

    total_candidates = await candidate_repo.count(company_filter)
    total_interviews = await session_repo.count(company_filter)
    total_selected = await candidate_repo.count({
        "status": {"$in": ["Selected", "Hired", "hired", "selected"]},
        **company_filter,
    })

    # Average time-to-hire from actual selected candidates
    selected_candidates = await candidate_repo.get_many(
        {"status": {"$in": ["Selected", "Hired"]}, "company_id": company_oid},
        limit=200,
    )
    time_deltas = []
    for c in selected_candidates:
        created = c.get("created_at")
        updated = c.get("updated_at")
        if created and updated and isinstance(created, datetime) and isinstance(updated, datetime):
            delta = (updated - created).days
            if 0 < delta < 365:
                time_deltas.append(delta)

    avg_time = round(sum(time_deltas) / len(time_deltas)) if time_deltas else 0
    avg_time_str = f"{avg_time} days" if avg_time > 0 else "N/A"

    offered = await candidate_repo.count({"status": "Offered", **company_filter})
    acceptance_rate = round((total_selected / offered) * 100, 1) if offered > 0 else 0.0
    acceptance_str = f"{acceptance_rate}%"

    return {
        "averageTimeToHire": {"value": avg_time_str, "positive": True},
        "offerAcceptanceRate": {"value": acceptance_str, "positive": True},
        "totalApplications": {"value": f"{total_candidates:,}", "positive": True},
        "totalInterviews": {"value": f"{total_interviews:,}", "positive": True},
        "selections": {"value": str(total_selected), "positive": True},
    }


# ──────────────────────────────────────────────────────────────────────
# GET /company/analytics/hiring-trend
# ──────────────────────────────────────────────────────────────────────

@router.get("/hiring-trend", summary="Get Monthly Hiring Trend")
async def get_hiring_trend(
    current_user: TokenPayload = Depends(require_role(UserRole.COMPANY)),
):
    """Aggregate monthly application and selection counts for the current year."""
    company_filter = {"company_id": ObjectId(current_user.sub)}
    current_year = datetime.utcnow().year
    all_candidates = await candidate_repo.get_many(query=company_filter, limit=5000)

    monthly_apps: dict = defaultdict(int)
    monthly_sel: dict = defaultdict(int)

    for c in all_candidates:
        created = c.get("created_at")
        if isinstance(created, datetime) and created.year == current_year:
            month_idx = created.month - 1
            monthly_apps[month_idx] += 1
            if c.get("status") in ("Selected", "Hired", "hired", "selected"):
                monthly_sel[month_idx] += 1

    trend = []
    for i, label in enumerate(MONTH_LABELS):
        trend.append({
            "month": label,
            "applications": monthly_apps.get(i, 0),
            "selections": monthly_sel.get(i, 0),
        })
    return trend


# ──────────────────────────────────────────────────────────────────────
# GET /company/analytics/candidate-sources
# ──────────────────────────────────────────────────────────────────────

@router.get("/candidate-sources", summary="Get Candidate Source Breakdown")
async def get_candidate_sources(
    current_user: TokenPayload = Depends(require_role(UserRole.COMPANY)),
):
    """Breakdown of candidates by source channel from MongoDB."""
    company_filter = {"company_id": ObjectId(current_user.sub)}
    all_candidates = await candidate_repo.get_many(query=company_filter, limit=5000)

    SOURCE_COLORS = {
        "LinkedIn": "#0A66C2",
        "Referrals": "#10B981",
        "Direct Search": "#8B5CF6",
        "Job Boards": "#3B82F6",
        "Agencies": "#F59E0B",
        "Other": "#64748B",
    }

    source_counts: dict = defaultdict(int)
    for c in all_candidates:
        src = c.get("source") or c.get("applied_via") or "Other"
        source_counts[src] += 1

    if not source_counts:
        return []

    total = sum(source_counts.values())
    result = []
    for src, count in sorted(source_counts.items(), key=lambda x: -x[1]):
        pct = round((count / total) * 100, 1)
        result.append({
            "source": src,
            "value": count,
            "percentage": pct,
            "color": SOURCE_COLORS.get(src, "#64748B"),
        })
    return result


# ──────────────────────────────────────────────────────────────────────
# GET /company/analytics/hiring-funnel
# ──────────────────────────────────────────────────────────────────────

@router.get("/hiring-funnel", summary="Get Hiring Funnel Stages")
async def get_hiring_funnel(
    current_user: TokenPayload = Depends(require_role(UserRole.COMPANY)),
):
    """Compute candidate pipeline conversion rates across status stages."""
    company_oid = ObjectId(current_user.sub)
    company_filter = {"company_id": company_oid}
    total = await candidate_repo.count(company_filter)

    STATUS_STAGES = [
        ("Applied", ["Applied", "New", "new", "applied"]),
        ("AI Screened", ["Screened", "AI Screened", "Shortlisted", "shortlisted"]),
        ("Assessments", ["Assessment", "Test Scheduled"]),
        ("Interviews", ["Interview Scheduled", "Interviewed", "in_progress"]),
        ("Offered", ["Offered", "offered"]),
        ("Hired", ["Selected", "Hired", "hired", "selected"]),
    ]

    applied_count = total or 1
    funnel = []
    for stage_label, statuses in STATUS_STAGES:
        count = 0
        for st in statuses:
            count += await candidate_repo.count({
                "status": st,
                "company_id": company_oid,
            })
        pct = round((count / applied_count) * 100, 1)
        funnel.append({
            "stage": stage_label,
            "count": count,
            "percentage": min(pct, 100),
            "label": f"{count} {stage_label}",
        })
    return funnel


# ──────────────────────────────────────────────────────────────────────
# GET /company/analytics/department-breakdown
# ──────────────────────────────────────────────────────────────────────

@router.get("/department-breakdown", summary="Get Department Hiring Breakdown")
async def get_department_breakdown(
    current_user: TokenPayload = Depends(require_role(UserRole.COMPANY)),
):
    """Aggregate open jobs, applicants, and hires per department."""
    company_oid = ObjectId(current_user.sub)
    company_filter = {"company_id": company_oid}

    jobs, _ = await job_repo.get_many(query=company_filter, limit=500)
    candidates = await candidate_repo.get_many(query=company_filter, limit=5000)

    dept_open_jobs: dict = defaultdict(int)
    dept_candidates: dict = defaultdict(int)
    dept_hires: dict = defaultdict(int)

    for j in jobs:
        dept = j.get("department") or "Other"
        if j.get("status", "").lower() in ("open", "active", "published"):
            dept_open_jobs[dept] += 1

    for c in candidates:
        dept = c.get("department") or c.get("applied_dept") or "Other"
        dept_candidates[dept] += 1
        if c.get("status") in ("Selected", "Hired", "hired", "selected"):
            dept_hires[dept] += 1

    all_depts = set(list(dept_open_jobs.keys()) + list(dept_candidates.keys()))

    if not all_depts:
        return []

    result = []
    for dept in sorted(all_depts):
        result.append({
            "department": dept,
            "openJobs": dept_open_jobs.get(dept, 0),
            "applicants": dept_candidates.get(dept, 0),
            "hires": dept_hires.get(dept, 0),
        })
    return result


# ──────────────────────────────────────────────────────────────────────
# GET /company/analytics/recruiter-performance
# ──────────────────────────────────────────────────────────────────────

@router.get("/recruiter-performance", summary="Get Recruiter Performance Scorecard")
async def get_recruiter_performance(
    current_user: TokenPayload = Depends(require_role(UserRole.COMPANY)),
):
    """Per-recruiter placement metrics from campaigns and candidates."""
    company_filter = {"company_id": ObjectId(current_user.sub)}
    campaigns = await campaign_repo.get_many(query=company_filter, limit=500)
    candidates = await candidate_repo.get_many(query=company_filter, limit=5000)

    recruiter_campaigns: dict = defaultdict(int)
    recruiter_selections: dict = defaultdict(int)
    recruiter_offered: dict = defaultdict(int)

    for camp in campaigns:
        recruiter = (
            camp.get("created_by")
            or camp.get("recruiter")
            or camp.get("recruiter_name")
        )
        if recruiter and camp.get("status", "").lower() in ("active", "open"):
            recruiter_campaigns[recruiter] += 1

    for c in candidates:
        recruiter = (
            c.get("assigned_to")
            or c.get("recruiter")
            or c.get("recruiter_name")
        )
        if recruiter:
            if c.get("status") in ("Selected", "Hired", "hired", "selected"):
                recruiter_selections[recruiter] += 1
            if c.get("status") in ("Offered", "Selected", "Hired", "offered"):
                recruiter_offered[recruiter] += 1

    all_recruiters = set(
        list(recruiter_campaigns.keys()) +
        list(recruiter_selections.keys())
    )

    if not all_recruiters:
        return []

    result = []
    for name in sorted(all_recruiters):
        selected = recruiter_selections.get(name, 0)
        offered = recruiter_offered.get(name, 0)
        acceptance_rate = round((selected / offered) * 100) if offered > 0 else 0
        result.append({
            "name": name,
            "activeCampaigns": recruiter_campaigns.get(name, 0),
            "averageTimeToHire": "N/A",
            "selections": selected,
            "offerAcceptanceRate": acceptance_rate,
        })

    return result[:10]


# ──────────────────────────────────────────────────────────────────────
# GET /company/analytics/yearly-comparison
# ──────────────────────────────────────────────────────────────────────

@router.get("/yearly-comparison", summary="Get Year-over-Year Applications Comparison")
async def get_yearly_comparison(
    current_user: TokenPayload = Depends(require_role(UserRole.COMPANY)),
):
    """Monthly application counts for the current and previous year."""
    company_filter = {"company_id": ObjectId(current_user.sub)}
    all_candidates = await candidate_repo.get_many(query=company_filter, limit=5000)

    current_year = datetime.utcnow().year
    prev_year = current_year - 1

    monthly_prev: dict = defaultdict(int)
    monthly_curr: dict = defaultdict(int)

    for c in all_candidates:
        created = c.get("created_at")
        if isinstance(created, datetime):
            m = created.month - 1
            if created.year == prev_year:
                monthly_prev[m] += 1
            elif created.year == current_year:
                monthly_curr[m] += 1

    result = []
    for i, label in enumerate(MONTH_LABELS[:7]):
        result.append({
            "month": label,
            f"year{prev_year}": monthly_prev.get(i, 0),
            f"year{current_year}": monthly_curr.get(i, 0),
        })
    return result
