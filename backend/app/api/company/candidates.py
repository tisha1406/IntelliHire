from datetime import datetime, UTC
# pyrefly: ignore [missing-import]
from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from app.repositories.candidate_repository import CandidateRepository
from app.repositories.campaign_repository import CampaignRepository
from app.repositories.interview_session_repository import InterviewSessionRepository
from app.repositories.interview_report_repository import InterviewReportRepository
from app.rbac.permissions import require_role, require_company_or_recruiter
from app.auth.jwt_handler import TokenPayload
from app.rbac.models import UserRole
from app.middleware.limits import check_limit
from app.repositories.company_repository import CompanyRepository

from app.schemas.response import (
    APIResponse,
    success_response,
)

from app.schemas.candidate_portal import (
    InviteCandidateRequest,
    InviteCandidateResponse,
)

from app.services.invitation_service import InvitationService

router = APIRouter(
    prefix="/company/candidates",
    tags=["Company - Candidates"],
)

# =============================================================
# FIXED ROUTE ORDER:
# Static/prefix routes (/interviews, /interviews/...) MUST come
# before wildcard routes (/{candidate_id}) to prevent FastAPI
# from matching "interviews" as a candidate_id.
# =============================================================


@router.post(
    "/invite",
    response_model=APIResponse[InviteCandidateResponse],
)
async def invite_candidate(
    req: InviteCandidateRequest,
    current_user: TokenPayload = Depends(
        require_company_or_recruiter
    ),
    _: TokenPayload = Depends(check_limit("max_candidates", "candidates_used")),
):
    service = InvitationService()
    # Resolve company_id by role
    company_id = (
        current_user.company_id
        if current_user.role.upper() == UserRole.RECRUITER.value.upper()
        else current_user.sub
    )

    try:
        
        assigned_recruiter_id = req.assigned_recruiter_id
        if current_user.role.upper() == UserRole.RECRUITER.value.upper():
            assigned_recruiter_id = current_user.recruiter_id

        result = await service.invite_candidate(
            company_id=company_id,
            campaign_id=req.campaign_id,
            name=req.name,
            email=req.email,
            assigned_recruiter_id=assigned_recruiter_id
        )

        company_repo = CompanyRepository()
        await company_repo.update_usage(company_id, "candidates_used", 1)
        
        # Log action
        from app.repositories.audit_log_repository import AuditLogRepository
        audit_repo = AuditLogRepository()
        await audit_repo.log_action(
            company_id=company_id,
            actor_id=current_user.sub,
            actor_name="Recruiter/Company Admin",
            actor_role=current_user.role,
            action="CREATED_CANDIDATE",
            target_entity="Candidate",
            target_name=req.name,
            metadata={"email": req.email, "campaign_id": req.campaign_id, "assigned_recruiter_id": assigned_recruiter_id}
        )

    except HTTPException:

        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e),
        )

    return success_response(
        data=InviteCandidateResponse(
            candidate=result["candidate"],
            credentials=result["credentials"]
        ),
        message="Candidate created successfully."
    )

@router.get("/")
async def get_candidates(
    current_user: TokenPayload = Depends(require_company_or_recruiter),
):
    repo = CandidateRepository()

    if current_user.role.upper() == UserRole.RECRUITER.value.upper():
        # Recruiter: only see candidates assigned to them
        candidates = await repo.list({"assigned_recruiter_id": ObjectId(current_user.recruiter_id)})
    else:
        # Company Admin: see all company candidates
        candidates = await repo.list({"company_id": ObjectId(current_user.company_id)})

    formatted = []
    for cand in candidates:
        formatted.append({
            "id": str(cand["_id"]),
            "name": cand.get("name"),
            "email": cand.get("email"),
            "phone": cand.get("phone", ""),
            "experience": cand.get("experience", ""),
            "education": cand.get("education", ""),
            "skills": cand.get("skills", []),
            "aiMatch": cand.get("aiMatch", 0),
            "ai_match": cand.get("aiMatch", 0),
            "resumeScore": cand.get("resumeScore", 0),
            "resume_score": cand.get("resumeScore", 0),
            "interviewScore": cand.get("interviewScore"),
            "interview_score": cand.get("interviewScore"),
            "currentStage": cand.get("currentStage", "Applied"),
            "current_stage": cand.get("currentStage", "Applied"),
            "status": cand.get("status", "Pending"),
            "timeline": cand.get("timeline", []),
            "aiRecommendations": cand.get("aiRecommendations", ""),
            "notes": cand.get("notes", ""),
            "campaign_id": str(cand["campaign_id"]) if cand.get("campaign_id") else None,
            "assigned_recruiter_id": str(cand["assigned_recruiter_id"]) if cand.get("assigned_recruiter_id") else None,
        })
    return formatted


class BulkAssignCandidatesRequest(BaseModel):
    candidate_ids: list[str]
    recruiter_id: str


@router.post("/bulk-assign")
async def bulk_assign_candidates(
    req: BulkAssignCandidatesRequest,
    current_user: TokenPayload = Depends(require_company_or_recruiter)
):
    repo = CandidateRepository()
    from app.repositories.recruiter_repository import RecruiterRepository
    recruiter_repo = RecruiterRepository()
    
    recruiter = await recruiter_repo.get_by_id(req.recruiter_id)
    if not recruiter or recruiter.get("company_id") != current_user.sub:
        raise HTTPException(status_code=400, detail="Invalid recruiter ID.")

    updated_count = 0
    from app.repositories.audit_log_repository import AuditLogRepository
    audit_repo = AuditLogRepository()

    for cid in req.candidate_ids:
        cand = await repo.get_by_id(cid)
        if cand and str(cand.get("company_id")) == current_user.sub:
            await repo.update(cid, {
                "assigned_recruiter_id": ObjectId(req.recruiter_id),
                "updated_at": datetime.now(UTC),
                "updated_by": ObjectId(current_user.sub),
                "updated_by_role": current_user.role
            })
            updated_count += 1
            
            # Log action
            await audit_repo.log_action(
                company_id=current_user.sub,
                actor_id=current_user.sub,
                actor_name="Recruiter/Company Admin",
                actor_role=current_user.role,
                action="REASSIGNED_CANDIDATES",
                target_entity="Candidate",
                target_id=cid,
                target_name=cand.get("name"),
                metadata={"new_recruiter_id": req.recruiter_id, "new_recruiter_name": recruiter.get("name")}
            )

    return success_response(data={"updated": updated_count}, message=f"Assigned {updated_count} candidates to {recruiter.get('name')}")


# ---------------------------------------------------------
# GET COMPANY INTERVIEWS & STATS
# (MUST be before /{candidate_id} routes)

# ---------------------------------------------------------
@router.get("/interviews")
async def get_company_interviews(
    current_user: TokenPayload = Depends(require_company_or_recruiter),
):
    session_repo = InterviewSessionRepository()
    report_repo = InterviewReportRepository()
    cand_repo = CandidateRepository()
    campaign_repo = CampaignRepository()
    
    # Resolve company_id by role
    company_id = (
        current_user.company_id
        if current_user.role.upper() == UserRole.RECRUITER.value.upper()
        else current_user.sub
    )

    if current_user.role.upper() == UserRole.RECRUITER.value.upper():
        # Get candidates assigned to this recruiter
        my_candidates = await cand_repo.get_many({"assigned_recruiter_id": ObjectId(current_user.recruiter_id)})
        my_candidate_ids = [c["_id"] for c in my_candidates]
        if not my_candidate_ids:
            sessions = []
        else:
            sessions = await session_repo.get_many({
                "company_id": ObjectId(company_id),
                "candidate_id": {"$in": my_candidate_ids}
            })
    else:
        sessions = await session_repo.get_many({"company_id": ObjectId(company_id)})

    formatted_interviews = []
    upcoming_count = 0
    completed_count = 0
    cancelled_count = 0
    score_sum = 0
    score_count = 0

    for sess in sessions:
        cand = await cand_repo.get_by_id(str(sess["candidate_id"]))
        camp = await campaign_repo.get_by_id(str(sess["campaign_id"]))
        rep = await report_repo.get_one({"session_id": sess["_id"]})

        status_val = "Scheduled"
        if sess.get("status") == "completed":
            status_val = "Completed"
            completed_count += 1
        elif sess.get("status") == "cancelled" or (cand and cand.get("status") == "Cancelled"):
            status_val = "Cancelled"
            cancelled_count += 1
        else:
            status_val = "Scheduled"
            upcoming_count += 1

        ai_score = rep.get("overall_score") if rep else None
        if ai_score is not None:
            score_sum += ai_score
            score_count += 1

        evaluation_data = None
        if rep:
            strengths_list = []
            if rep.get("strengths"):
                raw_s = rep["strengths"]
                if isinstance(raw_s, list):
                    strengths_list = raw_s
                else:
                    strengths_list = [s.strip() for s in raw_s.split("\n") if s.strip()]

            weaknesses_list = []
            if rep.get("weaknesses"):
                raw_w = rep["weaknesses"]
                if isinstance(raw_w, list):
                    weaknesses_list = raw_w
                else:
                    weaknesses_list = [w.strip() for w in raw_w.split("\n") if w.strip()]

            questions_list = []
            for turn in sess.get("turns", []):
                quality_score = turn.get("evaluation", {}).get("response_quality_score", 0)
                sentiment_val = (
                    "Excellent" if quality_score >= 9
                    else "Very Good" if quality_score >= 8
                    else "Good" if quality_score >= 7
                    else "Average"
                )
                questions_list.append({
                    "q": turn.get("question", ""),
                    "a": turn.get("answer_transcript", ""),
                    "sentiment": sentiment_val,
                    "score": int(turn.get("evaluation", {}).get("technical_score", 0) * 10),
                })

            evaluation_data = {
                "summary": rep.get("recruiter_summary") or rep.get("technical_skills_assessment", ""),
                "strengths": strengths_list,
                "weaknesses": weaknesses_list,
                "recommendation": (
                    rep.get("resume_match_analysis", {}).get("consistency_notes") or "Review Candidate"
                ),
                "questions": questions_list,
            }

        formatted_interviews.append({
            "id": str(sess["_id"]),
            "candidate": cand.get("name") if cand else "Unknown",
            "candidate_id": str(sess["candidate_id"]),
            "position": camp.get("role_target") if camp else "Software Engineer",
            "interviewer": (
                f"AI Agent ({camp['voice_config']['voice_id']})"
                if (camp and camp.get("voice_config"))
                else "AI Agent"
            ),
            "date": (
                sess["created_at"].strftime("%Y-%m-%d")
                if sess.get("created_at")
                else "2026-07-29"
            ),
            "time": (
                sess["created_at"].strftime("%H:%M")
                if sess.get("created_at")
                else "12:00"
            ),
            "status": status_val,
            "aiScore": ai_score,
            "evaluation": evaluation_data,
        })

    avg_score = round(score_sum / score_count) if score_count > 0 else 0

    return {
        "stats": {
            "upcoming": upcoming_count,
            "completed": completed_count,
            "cancelled": cancelled_count,
            "averageScore": avg_score,
        },
        "interviews": formatted_interviews,
    }


# ---------------------------------------------------------
# CANCEL INTERVIEW SESSION
# (MUST be before /{candidate_id} routes)
# ---------------------------------------------------------
@router.patch("/interviews/{session_id}/cancel")
async def cancel_company_interview(
    session_id: str,
    current_user: TokenPayload = Depends(require_company_or_recruiter),
):
    session_repo = InterviewSessionRepository()
    cand_repo = CandidateRepository()

    session = await session_repo.get_by_id(session_id)
    if not session or str(session.get("company_id")) != str(current_user.company_id):
        raise HTTPException(status_code=404, detail="Interview session not found")

    await session_repo.update(session_id, {"status": "cancelled"})

    candidate_id = str(session["candidate_id"])
    await cand_repo.update(candidate_id, {"status": "Cancelled", "currentStage": "Rejected"})

    cand = await cand_repo.get_by_id(candidate_id)
    if cand:
        timeline = cand.get("timeline", [])
        timeline.append({
            "stage": "AI Interview",
            "date": datetime.now(UTC).strftime("%Y-%m-%d"),
            "status": "cancelled",
            "notes": "Interview session cancelled by company recruiter",
        })
        await cand_repo.update(candidate_id, {"timeline": timeline})

    return {"message": "AI Interview session cancelled successfully."}


# ---------------------------------------------------------
# SCHEDULE NEW INTERVIEW FROM PORTAL
# (MUST be before /{candidate_id} routes)
# ---------------------------------------------------------
@router.post("/interviews/schedule")
async def schedule_new_company_interview(
    data: dict,
    current_user: TokenPayload = Depends(require_company_or_recruiter),
):
    cand_repo = CandidateRepository()
    campaign_repo = CampaignRepository()
    session_repo = InterviewSessionRepository()

    candidate_id = data.get("candidate_id")
    campaign_id = data.get("campaign_id")

    if not candidate_id or not campaign_id:
        raise HTTPException(status_code=400, detail="candidate_id and campaign_id are required")

    cand = await cand_repo.get_by_id(candidate_id)
# Verify access
    company_id = current_user.company_id if current_user.role.upper() == "RECRUITER" else current_user.sub
    if not cand or str(cand.get("company_id")) != str(company_id):
        raise HTTPException(status_code=404, detail="Candidate not found")
    if current_user.role.upper() == "RECRUITER" and str(cand.get("assigned_recruiter_id")) != str(current_user.recruiter_id):
        raise HTTPException(status_code=404, detail="Candidate not found (not assigned)")

    camp = await campaign_repo.get_by_id(campaign_id)
    if not camp or str(camp.get("company_id")) != str(current_user.company_id):
        raise HTTPException(status_code=404, detail="Campaign not found")

    session_data = {
        "company_id": ObjectId(current_user.company_id),
        "campaign_id": ObjectId(campaign_id),
        "candidate_id": ObjectId(candidate_id),
        "language": "English",
        "interview_mode": "Balanced",
        "status": "in_progress",
        "question_budget": {
            "min_questions": 5,
            "max_questions": 10,
            "complexity_scores": {"experience": 7.0, "skills": 7.0, "projects": 7.0},
        },
        "interview_state": {
            "current_question": "Please introduce yourself.",
            "current_topic": "Introduction",
            "difficulty": "medium",
            "interview_phase": "active",
        },
        "turns": [],
        "created_at": datetime.now(UTC),
    }
    session_id = await session_repo.create(session_data)

    await cand_repo.update(candidate_id, {
        "currentStage": "Interview Scheduled",
        "current_stage": "Interview Scheduled",
        "status": "Scheduled",
    })

    timeline = cand.get("timeline", [])
    timeline.append({
        "stage": "AI Interview",
        "date": datetime.now(UTC).strftime("%Y-%m-%d"),
        "status": "scheduled",
        "notes": "Interview scheduled by recruiter",
    })
    await cand_repo.update(candidate_id, {"timeline": timeline})

    return {
        "message": "AI Interview scheduled successfully",
        "session_id": str(session_id),
    }


# =============================================================
# WILDCARD /{candidate_id} ROUTES (must come after all static routes)
# =============================================================


# ---------------------------------------------------------
# GET ONE CANDIDATE
# ---------------------------------------------------------
@router.get("/{candidate_id}")
async def get_candidate(
    candidate_id: str,
    current_user: TokenPayload = Depends(require_company_or_recruiter),
):
    repo = CandidateRepository()
    cand = await repo.get(candidate_id)
# Verify access
    company_id = current_user.company_id if current_user.role.upper() == "RECRUITER" else current_user.sub
    if not cand or str(cand.get("company_id")) != str(company_id):
        raise HTTPException(status_code=404, detail="Candidate not found")
    if current_user.role.upper() == "RECRUITER" and str(cand.get("assigned_recruiter_id")) != str(current_user.recruiter_id):
        raise HTTPException(status_code=404, detail="Candidate not found (not assigned)")

    return {
        "id": str(cand["_id"]),
        "name": cand.get("name"),
        "email": cand.get("email"),
        "phone": cand.get("phone", ""),
        "experience": cand.get("experience", ""),
        "education": cand.get("education", ""),
        "skills": cand.get("skills", []),
        "aiMatch": cand.get("aiMatch", 0),
        "ai_match": cand.get("aiMatch", 0),
        "resumeScore": cand.get("resumeScore", 0),
        "resume_score": cand.get("resumeScore", 0),
        "interviewScore": cand.get("interviewScore"),
        "interview_score": cand.get("interviewScore"),
        "currentStage": cand.get("currentStage", "Applied"),
        "current_stage": cand.get("currentStage", "Applied"),
        "status": cand.get("status", "Pending"),
        "timeline": cand.get("timeline", []),
        "aiRecommendations": cand.get("aiRecommendations", ""),
        "notes": cand.get("notes", ""),
    }


# ---------------------------------------------------------
# CREATE CANDIDATE
# ---------------------------------------------------------
@router.post("/")
async def create_candidate(
    candidate: dict,
    current_user: TokenPayload = Depends(require_company_or_recruiter),
    _: TokenPayload = Depends(check_limit("max_candidates", "candidates_used")),
):
    repo = CandidateRepository()
    company_id = current_user.company_id if current_user.role.upper() == "RECRUITER" else current_user.sub
    candidate["company_id"] = ObjectId(company_id)
    if current_user.role.upper() == "RECRUITER":
        candidate["assigned_recruiter_id"] = ObjectId(current_user.recruiter_id)
    if "campaign_id" in candidate and candidate["campaign_id"]:
        candidate["campaign_id"] = ObjectId(candidate["campaign_id"])
    if "assigned_recruiter_id" in candidate and candidate["assigned_recruiter_id"]:
        candidate["assigned_recruiter_id"] = ObjectId(candidate["assigned_recruiter_id"])

    candidate.setdefault("aiMatch", 0)
    candidate.setdefault("resumeScore", 0)
    candidate.setdefault("currentStage", "Applied")
    candidate.setdefault("status", "Pending")

    cand_id = await repo.create(candidate)
    
    company_repo = CompanyRepository()
    company_id = current_user.company_id if current_user.role.upper() == "RECRUITER" else current_user.sub
    await company_repo.update_usage(company_id, "candidates_used", 1)
    
    return {
        "message": "Candidate created",
        "id": str(cand_id),
    }


# ---------------------------------------------------------
# UPDATE CANDIDATE
# ---------------------------------------------------------
@router.put("/{candidate_id}")
async def update_candidate(
    candidate_id: str,
    data: dict,
    current_user: TokenPayload = Depends(require_company_or_recruiter),
):
    repo = CandidateRepository()
    cand = await repo.get(candidate_id)
# Verify access
    company_id = current_user.company_id if current_user.role.upper() == "RECRUITER" else current_user.sub
    if not cand or str(cand.get("company_id")) != str(company_id):
        raise HTTPException(status_code=404, detail="Candidate not found")
    if current_user.role.upper() == "RECRUITER" and str(cand.get("assigned_recruiter_id")) != str(current_user.recruiter_id):
        raise HTTPException(status_code=404, detail="Candidate not found (not assigned)")

    data.pop("_id", None)
    data.pop("id", None)
    data.pop("company_id", None)
    if "campaign_id" in data and data["campaign_id"]:
        data["campaign_id"] = ObjectId(data["campaign_id"])
    if "assigned_recruiter_id" in data and data["assigned_recruiter_id"]:
        data["assigned_recruiter_id"] = ObjectId(data["assigned_recruiter_id"])

    await repo.update(candidate_id, data)
    return {"message": "Candidate updated"}


# ---------------------------------------------------------
# DELETE CANDIDATE
# ---------------------------------------------------------
@router.delete("/{candidate_id}")
async def delete_candidate(
    candidate_id: str,
    current_user: TokenPayload = Depends(require_company_or_recruiter),
):
    repo = CandidateRepository()
    cand = await repo.get(candidate_id)
# Verify access
    company_id = current_user.company_id if current_user.role.upper() == "RECRUITER" else current_user.sub
    if not cand or str(cand.get("company_id")) != str(company_id):
        raise HTTPException(status_code=404, detail="Candidate not found")
    if current_user.role.upper() == "RECRUITER" and str(cand.get("assigned_recruiter_id")) != str(current_user.recruiter_id):
        raise HTTPException(status_code=404, detail="Candidate not found (not assigned)")

    await repo.delete(candidate_id)

    company_repo = CompanyRepository()
    company_id = current_user.company_id if current_user.role.upper() == "RECRUITER" else current_user.sub
    await company_repo.update_usage(company_id, "candidates_used", -1)

    return {"message": "Candidate deleted"}


# ---------------------------------------------------------
# SHORTLIST CANDIDATE
# ---------------------------------------------------------
@router.patch("/{candidate_id}/shortlist")
async def shortlist_candidate(
    candidate_id: str,
    current_user: TokenPayload = Depends(require_company_or_recruiter),
):
    repo = CandidateRepository()
    cand = await repo.get(candidate_id)
# Verify access
    company_id = current_user.company_id if current_user.role.upper() == "RECRUITER" else current_user.sub
    if not cand or str(cand.get("company_id")) != str(company_id):
        raise HTTPException(status_code=404, detail="Candidate not found")
    if current_user.role.upper() == "RECRUITER" and str(cand.get("assigned_recruiter_id")) != str(current_user.recruiter_id):
        raise HTTPException(status_code=404, detail="Candidate not found (not assigned)")

    update_data = {
        "status": "Shortlisted",
        "currentStage": "Selected",
        "current_stage": "Selected",
    }
    await repo.update(candidate_id, update_data)

    timeline = cand.get("timeline", [])
    timeline.append({
        "stage": "Shortlisted",
        "date": datetime.now(UTC).strftime("%Y-%m-%d"),
        "status": "completed",
        "notes": "Shortlisted by recruiter",
    })
    await repo.update(candidate_id, {"timeline": timeline})

    return {"message": "Candidate shortlisted"}


# ---------------------------------------------------------
# REJECT CANDIDATE
# ---------------------------------------------------------
@router.patch("/{candidate_id}/reject")
async def reject_candidate(
    candidate_id: str,
    current_user: TokenPayload = Depends(require_company_or_recruiter),
):
    repo = CandidateRepository()
    cand = await repo.get(candidate_id)
# Verify access
    company_id = current_user.company_id if current_user.role.upper() == "RECRUITER" else current_user.sub
    if not cand or str(cand.get("company_id")) != str(company_id):
        raise HTTPException(status_code=404, detail="Candidate not found")
    if current_user.role.upper() == "RECRUITER" and str(cand.get("assigned_recruiter_id")) != str(current_user.recruiter_id):
        raise HTTPException(status_code=404, detail="Candidate not found (not assigned)")

    update_data = {
        "status": "Rejected",
        "currentStage": "Rejected",
        "current_stage": "Rejected",
    }
    await repo.update(candidate_id, update_data)

    timeline = cand.get("timeline", [])
    timeline.append({
        "stage": "Rejected",
        "date": datetime.now(UTC).strftime("%Y-%m-%d"),
        "status": "completed",
        "notes": "Rejected by recruiter",
    })
    await repo.update(candidate_id, {"timeline": timeline})

    return {"message": "Candidate rejected"}


# ---------------------------------------------------------
# SCHEDULE INTERVIEW (from Candidates page)
# ---------------------------------------------------------
@router.patch("/{candidate_id}/schedule")
async def schedule_interview(
    candidate_id: str,
    current_user: TokenPayload = Depends(require_company_or_recruiter),
):
    repo = CandidateRepository()
    cand = await repo.get(candidate_id)
# Verify access
    company_id = current_user.company_id if current_user.role.upper() == "RECRUITER" else current_user.sub
    if not cand or str(cand.get("company_id")) != str(company_id):
        raise HTTPException(status_code=404, detail="Candidate not found")
    if current_user.role.upper() == "RECRUITER" and str(cand.get("assigned_recruiter_id")) != str(current_user.recruiter_id):
        raise HTTPException(status_code=404, detail="Candidate not found (not assigned)")

    update_data = {
        "currentStage": "Interview Scheduled",
        "current_stage": "Interview Scheduled",
        "status": "Scheduled",
    }
    await repo.update(candidate_id, update_data)

    timeline = cand.get("timeline", [])
    timeline.append({
        "stage": "AI Interview",
        "date": datetime.now(UTC).strftime("%Y-%m-%d"),
        "status": "scheduled",
        "notes": "Interview scheduled by recruiter",
    })
    await repo.update(candidate_id, {"timeline": timeline})

    # Create session if candidate has a campaign_id and no existing session
    if cand.get("campaign_id"):
        session_repo = InterviewSessionRepository()
        existing_session = await session_repo.get_one({"candidate_id": ObjectId(candidate_id)})
        if not existing_session:
            session_data = {
                "company_id": ObjectId(current_user.company_id),
                "campaign_id": ObjectId(str(cand["campaign_id"])),
                "candidate_id": ObjectId(candidate_id),
                "language": "English",
                "interview_mode": "Balanced",
                "status": "in_progress",
                "question_budget": {
                    "min_questions": 5,
                    "max_questions": 10,
                    "complexity_scores": {"experience": 7.0, "skills": 7.0, "projects": 7.0},
                },
                "interview_state": {
                    "current_question": "Please introduce yourself.",
                    "current_topic": "Introduction",
                    "difficulty": "medium",
                    "interview_phase": "active",
                },
                "turns": [],
                "created_at": datetime.now(UTC),
            }
            await session_repo.create(session_data)

    return {"message": "Interview scheduled"}


# ---------------------------------------------------------
# REASSIGN CANDIDATE
# ---------------------------------------------------------
class ReassignRequest(BaseModel):
    recruiter_id: str

@router.put("/{candidate_id}/reassign", response_model=APIResponse[dict])
async def reassign_candidate(
    candidate_id: str,
    request: ReassignRequest,
    current_user: TokenPayload = Depends(require_company_or_recruiter),
):
    repo = CandidateRepository()
    cand = await repo.get(candidate_id)
# Verify access
    company_id = current_user.company_id if current_user.role.upper() == "RECRUITER" else current_user.sub
    if not cand or str(cand.get("company_id")) != str(company_id):
        raise HTTPException(status_code=404, detail="Candidate not found")
    if current_user.role.upper() == "RECRUITER" and str(cand.get("assigned_recruiter_id")) != str(current_user.recruiter_id):
        raise HTTPException(status_code=404, detail="Candidate not found (not assigned)")

    # Verify the new recruiter belongs to the company
    from app.repositories.recruiter_repository import RecruiterRepository
    recruiter_repo = RecruiterRepository()
    recruiter = await recruiter_repo.get_by_id(request.recruiter_id)
    if not recruiter or str(recruiter.get("company_id")) != str(current_user.company_id):
        raise HTTPException(status_code=400, detail="Recruiter not found in this company")

    await repo.update(candidate_id, {
        "assigned_recruiter_id": ObjectId(request.recruiter_id),
        "updated_at": datetime.now(UTC)
    })

    return success_response(message="Candidate reassigned successfully")

# ---------------------------------------------------------
# SUSPEND CANDIDATE
# ---------------------------------------------------------
@router.patch("/{candidate_id}/suspend")
async def suspend_candidate(
    candidate_id: str,
    current_user: TokenPayload = Depends(require_company_or_recruiter),
):
    repo = CandidateRepository()
    cand = await repo.get(candidate_id)
    company_id = current_user.company_id if current_user.role.upper() == "RECRUITER" else current_user.sub
    
    if not cand or str(cand.get("company_id")) != str(company_id):
        raise HTTPException(status_code=404, detail="Candidate not found")
    if current_user.role.upper() == "RECRUITER" and str(cand.get("assigned_recruiter_id")) != str(current_user.recruiter_id):
        raise HTTPException(status_code=404, detail="Candidate not found (not assigned)")

    await repo.update(candidate_id, {"status": "suspended", "updated_at": datetime.now(UTC)})
    
    from app.repositories.user_repository import UserRepository
    user_repo = UserRepository()
    if cand.get("user_id"):
        await user_repo.update(str(cand["user_id"]), {"is_active": False, "updated_at": datetime.now(UTC)})

    return success_response(message="Candidate suspended successfully")

# ---------------------------------------------------------
# ACTIVATE CANDIDATE
# ---------------------------------------------------------
@router.patch("/{candidate_id}/activate")
async def activate_candidate(
    candidate_id: str,
    current_user: TokenPayload = Depends(require_company_or_recruiter),
):
    repo = CandidateRepository()
    cand = await repo.get(candidate_id)
    company_id = current_user.company_id if current_user.role.upper() == "RECRUITER" else current_user.sub
    
    if not cand or str(cand.get("company_id")) != str(company_id):
        raise HTTPException(status_code=404, detail="Candidate not found")
    if current_user.role.upper() == "RECRUITER" and str(cand.get("assigned_recruiter_id")) != str(current_user.recruiter_id):
        raise HTTPException(status_code=404, detail="Candidate not found (not assigned)")

    await repo.update(candidate_id, {"status": "active", "updated_at": datetime.now(UTC)})
    
    from app.repositories.user_repository import UserRepository
    user_repo = UserRepository()
    if cand.get("user_id"):
        await user_repo.update(str(cand["user_id"]), {"is_active": True, "updated_at": datetime.now(UTC)})

    return success_response(message="Candidate activated successfully")

# ---------------------------------------------------------
# RESET CREDENTIALS
# ---------------------------------------------------------
@router.post("/{candidate_id}/reset-credentials")
async def reset_credentials(
    candidate_id: str,
    current_user: TokenPayload = Depends(require_company_or_recruiter),
):
    repo = CandidateRepository()
    cand = await repo.get(candidate_id)
    company_id = current_user.company_id if current_user.role.upper() == "RECRUITER" else current_user.sub
    
    if not cand or str(cand.get("company_id")) != str(company_id):
        raise HTTPException(status_code=404, detail="Candidate not found")
    if current_user.role.upper() == "RECRUITER" and str(cand.get("assigned_recruiter_id")) != str(current_user.recruiter_id):
        raise HTTPException(status_code=404, detail="Candidate not found (not assigned)")

    service = InvitationService()
    new_password = service._generate_temporary_password()
    from app.auth.jwt_handler import hash_password
    hashed_password = hash_password(new_password)

    from app.repositories.user_repository import UserRepository
    user_repo = UserRepository()
    if cand.get("user_id"):
        await user_repo.update(str(cand["user_id"]), {
            "password_hash": hashed_password,
            "must_change_password": False,
            "updated_at": datetime.now(UTC)
        })

    return success_response(data={
        "candidate": {
            "id": str(cand.get("_id")),
            "name": cand.get("name"),
            "email": cand.get("email"),
            "username": cand.get("email"),
            "company_id": str(cand.get("company_id")),
            "campaign_id": str(cand.get("campaign_id")),
            "assigned_recruiter_id": str(cand.get("assigned_recruiter_id")) if cand.get("assigned_recruiter_id") else None,
            "status": cand.get("status")
        },
        "credentials": {
            "username": cand.get("email"),
            "temporary_password": new_password
        }
    }, message="Candidate credentials reset successfully")