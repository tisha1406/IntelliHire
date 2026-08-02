from datetime import datetime, UTC
from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, status

from app.repositories.candidate_repository import CandidateRepository
from app.repositories.campaign_repository import CampaignRepository
from app.repositories.interview_session_repository import InterviewSessionRepository
from app.repositories.interview_report_repository import InterviewReportRepository
from app.rbac.permissions import require_role
from app.auth.jwt_handler import TokenPayload
from app.rbac.models import UserRole

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
        require_role(UserRole.COMPANY)
    ),
):
    service = InvitationService()

    try:

        invitation_token = await service.invite_candidate(
            company_id=current_user.company_id,
            campaign_id=req.campaign_id,
            name=req.name,
            email=req.email,
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
            candidate_id="temp",
            user_id="temp",
            invitation_token=invitation_token,
            message="Invitation sent successfully.",
        )

    )

# ---------------------------------------------------------
# GET ALL CANDIDATES
# ---------------------------------------------------------
@router.get("/")
async def get_candidates(
    current_user: TokenPayload = Depends(require_role(UserRole.COMPANY)),
):
    repo = CandidateRepository()
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
        })
    return formatted


# ---------------------------------------------------------
# GET COMPANY INTERVIEWS & STATS
# (MUST be before /{candidate_id} routes)
# ---------------------------------------------------------
@router.get("/interviews")
async def get_company_interviews(
    current_user: TokenPayload = Depends(require_role(UserRole.COMPANY)),
):
    session_repo = InterviewSessionRepository()
    report_repo = InterviewReportRepository()
    cand_repo = CandidateRepository()
    campaign_repo = CampaignRepository()

    sessions = await session_repo.get_many({"company_id": ObjectId(current_user.company_id)})

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
    current_user: TokenPayload = Depends(require_role(UserRole.COMPANY)),
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
    current_user: TokenPayload = Depends(require_role(UserRole.COMPANY)),
):
    cand_repo = CandidateRepository()
    campaign_repo = CampaignRepository()
    session_repo = InterviewSessionRepository()

    candidate_id = data.get("candidate_id")
    campaign_id = data.get("campaign_id")

    if not candidate_id or not campaign_id:
        raise HTTPException(status_code=400, detail="candidate_id and campaign_id are required")

    cand = await cand_repo.get_by_id(candidate_id)
    if not cand or str(cand.get("company_id")) != str(current_user.company_id):
        raise HTTPException(status_code=404, detail="Candidate not found")

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
    current_user: TokenPayload = Depends(require_role(UserRole.COMPANY)),
):
    repo = CandidateRepository()
    cand = await repo.get(candidate_id)
    if not cand or str(cand.get("company_id")) != str(current_user.company_id):
        raise HTTPException(status_code=404, detail="Candidate not found")

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
    current_user: TokenPayload = Depends(require_role(UserRole.COMPANY)),
):
    repo = CandidateRepository()
    candidate["company_id"] = ObjectId(current_user.company_id)
    if "campaign_id" in candidate:
        candidate["campaign_id"] = ObjectId(candidate["campaign_id"])

    candidate.setdefault("aiMatch", 0)
    candidate.setdefault("resumeScore", 0)
    candidate.setdefault("currentStage", "Applied")
    candidate.setdefault("status", "Pending")

    cand_id = await repo.create(candidate)
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
    current_user: TokenPayload = Depends(require_role(UserRole.COMPANY)),
):
    repo = CandidateRepository()
    cand = await repo.get(candidate_id)
    if not cand or str(cand.get("company_id")) != str(current_user.company_id):
        raise HTTPException(status_code=404, detail="Candidate not found")

    data.pop("_id", None)
    data.pop("id", None)
    data.pop("company_id", None)
    if "campaign_id" in data:
        data["campaign_id"] = ObjectId(data["campaign_id"])

    await repo.update(candidate_id, data)
    return {"message": "Candidate updated"}


# ---------------------------------------------------------
# DELETE CANDIDATE
# ---------------------------------------------------------
@router.delete("/{candidate_id}")
async def delete_candidate(
    candidate_id: str,
    current_user: TokenPayload = Depends(require_role(UserRole.COMPANY)),
):
    repo = CandidateRepository()
    cand = await repo.get(candidate_id)
    if not cand or str(cand.get("company_id")) != str(current_user.company_id):
        raise HTTPException(status_code=404, detail="Candidate not found")

    await repo.delete(candidate_id)
    return {"message": "Candidate deleted"}


# ---------------------------------------------------------
# SHORTLIST CANDIDATE
# ---------------------------------------------------------
@router.patch("/{candidate_id}/shortlist")
async def shortlist_candidate(
    candidate_id: str,
    current_user: TokenPayload = Depends(require_role(UserRole.COMPANY)),
):
    repo = CandidateRepository()
    cand = await repo.get(candidate_id)
    if not cand or str(cand.get("company_id")) != str(current_user.company_id):
        raise HTTPException(status_code=404, detail="Candidate not found")

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
    current_user: TokenPayload = Depends(require_role(UserRole.COMPANY)),
):
    repo = CandidateRepository()
    cand = await repo.get(candidate_id)
    if not cand or str(cand.get("company_id")) != str(current_user.company_id):
        raise HTTPException(status_code=404, detail="Candidate not found")

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
    current_user: TokenPayload = Depends(require_role(UserRole.COMPANY)),
):
    repo = CandidateRepository()
    cand = await repo.get(candidate_id)
    if not cand or str(cand.get("company_id")) != str(current_user.company_id):
        raise HTTPException(status_code=404, detail="Candidate not found")

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