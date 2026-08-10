"""
Company Team Management API
Manages the company's recruiting team by reading/writing to the `recruiters` collection.
All endpoints require COMPANY authentication and are automatically scoped to the
authenticated company's company_id — no frontend-provided company_id is trusted.

Decision: Team Members == Recruiters. One collection, one concept.
"""
from datetime import datetime, timezone
from typing import Optional, List

from bson import ObjectId
from fastapi import APIRouter, HTTPException, Query, Depends, status
from pydantic import BaseModel, EmailStr

from app.auth.jwt_handler import TokenPayload
from app.rbac.models import UserRole
from app.rbac.permissions import require_role
from app.repositories.recruiter_repository import RecruiterRepository
from app.repositories.company_repository import CompanyRepository
from app.db.mongo import serialize_mongo_doc
from app.middleware.limits import check_limit

router = APIRouter(prefix="/company/team", tags=["Company Team"])


# ──────────────────────────────────────────────────────────────────────
# Request / Response models
# ──────────────────────────────────────────────────────────────────────

class TeamMemberResponse(BaseModel):
    id: str
    name: str
    email: str
    role: str
    designation: Optional[str] = ""
    department: Optional[str] = ""
    phone: Optional[str] = ""
    status: str
    company_id: Optional[str] = None
    created_at: Optional[str] = None
    temporary_password: Optional[str] = None
    
    # Advanced Profile Fields
    employee_id: Optional[str] = None
    joining_date: Optional[str] = None
    skills: List[str] = []
    timezone: Optional[str] = None
    language: Optional[str] = None
    profile_photo: Optional[str] = None
    signature: Optional[str] = None
    bio: Optional[str] = None
    
    # Status tracking
    last_active: Optional[str] = None
    last_login: Optional[str] = None
    is_online: bool = False
    is_deleted: bool = False


class InviteMemberRequest(BaseModel):
    name: str
    email: EmailStr
    role: str = "recruiter"
    designation: Optional[str] = None
    department: Optional[str] = None
    phone: Optional[str] = None


class UpdateMemberRequest(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None
    designation: Optional[str] = None
    department: Optional[str] = None
    phone: Optional[str] = None
    status: Optional[str] = None
    
    # Advanced Profile Fields
    employee_id: Optional[str] = None
    joining_date: Optional[str] = None
    skills: Optional[List[str]] = None
    timezone: Optional[str] = None
    language: Optional[str] = None
    profile_photo: Optional[str] = None
    signature: Optional[str] = None
    bio: Optional[str] = None


# ──────────────────────────────────────────────────────────────────────
# Helper
# ──────────────────────────────────────────────────────────────────────

def _format_member(doc: dict) -> TeamMemberResponse:
    created = doc.get("created_at")
    if isinstance(created, datetime):
        created_str = created.isoformat()
    else:
        created_str = str(created) if created else None

    return TeamMemberResponse(
        id=str(doc["_id"]),
        name=doc.get("name", ""),
        email=doc.get("email", ""),
        role=doc.get("role", "recruiter"),
        designation=doc.get("designation", ""),
        department=doc.get("department", ""),
        phone=doc.get("phone", ""),
        status=doc.get("status", "active"),
        company_id=doc.get("company_id"),
        created_at=created_str,
        temporary_password=doc.get("temporary_password"),
        employee_id=doc.get("employee_id"),
        joining_date=str(doc.get("joining_date")) if doc.get("joining_date") else None,
        skills=doc.get("skills", []),
        timezone=doc.get("timezone"),
        language=doc.get("language"),
        profile_photo=doc.get("profile_photo"),
        signature=doc.get("signature"),
        bio=doc.get("bio"),
        last_active=str(doc.get("last_active")) if doc.get("last_active") else None,
        last_login=str(doc.get("last_login")) if doc.get("last_login") else None,
        is_online=doc.get("is_online", False),
        is_deleted=doc.get("is_deleted", False)
    )


# ──────────────────────────────────────────────────────────────────────
# GET /company/team
# ──────────────────────────────────────────────────────────────────────

@router.get("", response_model=List[TeamMemberResponse], summary="Get Team Members")
async def get_team(
    search: Optional[str] = Query(None),
    role: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    limit: int = Query(100, ge=1),
    offset: int = Query(0, ge=0),
    current_user: TokenPayload = Depends(require_role(UserRole.COMPANY)),
):
    """
    Return all recruiters (team members) belonging to this company.
    Filtered by company_id from JWT — not trusted from request.
    """
    repo = RecruiterRepository()
    query: dict = {"company_id": current_user.sub}

    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"email": {"$regex": search, "$options": "i"}},
            {"designation": {"$regex": search, "$options": "i"}},
        ]
    if role:
        query["role"] = {"$regex": f"^{role}$", "$options": "i"}
    if status_filter:
        query["status"] = status_filter
        
    # By default, do not return deleted recruiters unless requested
    if "is_deleted" not in query:
        query["is_deleted"] = {"$ne": True}

    members = await repo.get_many(query=query, limit=limit, skip=offset)
    return [_format_member(m) for m in members]


# ──────────────────────────────────────────────────────────────────────
# POST /company/team
# ──────────────────────────────────────────────────────────────────────

@router.post("", response_model=TeamMemberResponse, status_code=status.HTTP_201_CREATED, summary="Add Team Member")
async def invite_team_member(
    payload: InviteMemberRequest,
    current_user: TokenPayload = Depends(require_role(UserRole.COMPANY)),
    _: TokenPayload = Depends(check_limit("max_recruiters", "recruiters_used")),
):
    """
    Add a new recruiter to this company's team.
    company_id is taken from the authenticated JWT — never from the request.
    """
    repo = RecruiterRepository()

    # Check for duplicate email within this company
    existing = await repo.get_by_email(payload.email)
    if existing and existing.get("company_id") == current_user.sub:
        raise HTTPException(
            status_code=409,
            detail="A team member with this email already exists in your company.",
        )

    # 1. Generate a temporary password
    import secrets
    import string
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    temp_password = "".join(secrets.choice(alphabet) for _ in range(12))

    # 2. Check if user exists in global users collection
    from app.repositories.user_repository import UserRepository
    from app.auth.jwt_handler import hash_password
    user_repo = UserRepository()
    existing_user = await user_repo.get_by_email(payload.email)
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="User with this email already exists globally."
        )

    doc = {
        "name": payload.name,
        "email": payload.email,
        "role": payload.role,
        "designation": payload.designation or payload.role.title(),
        "department": payload.department or "Recruitment",
        "phone": payload.phone or "",
        "status": "active",
        "company_id": current_user.sub,   # always from JWT
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }

    inserted_id = await repo.create(doc)
    doc["_id"] = ObjectId(inserted_id)

    # 3. Create the user record
    user_doc = {
        "email": payload.email,
        "password_hash": hash_password(temp_password),
        "role": "recruiter",
        "company_id": ObjectId(current_user.sub),
        "recruiter_id": ObjectId(inserted_id),
        "is_active": True,
        "must_change_password": True,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    }
    await user_repo.create(user_doc)

    # Return temp password so company admin can share it
    doc["temporary_password"] = temp_password

    company_repo = CompanyRepository()
    await company_repo.update_usage(current_user.sub, "recruiters_used", 1)

    return _format_member(doc)


# ──────────────────────────────────────────────────────────────────────
# PATCH /company/team/{member_id}
# ──────────────────────────────────────────────────────────────────────

@router.patch("/{member_id}", response_model=TeamMemberResponse, summary="Update Team Member")
async def update_team_member(
    member_id: str,
    payload: UpdateMemberRequest,
    current_user: TokenPayload = Depends(require_role(UserRole.COMPANY)),
):
    """
    Update a recruiter's details. Validates the recruiter belongs to this company.
    """
    repo = RecruiterRepository()
    member = await repo.get_by_id(member_id)

    if not member or member.get("company_id") != current_user.sub:
        raise HTTPException(status_code=404, detail="Team member not found.")

    update_data = {k: v for k, v in payload.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update.")

    update_data["updated_at"] = datetime.now(timezone.utc)
    await repo.update(member_id, update_data)

    updated = await repo.get_by_id(member_id)
    return _format_member(updated)


# ──────────────────────────────────────────────────────────────────────
# DELETE /company/team/{member_id}
# ──────────────────────────────────────────────────────────────────────

@router.delete("/{member_id}", summary="Remove Team Member")
async def remove_team_member(
    member_id: str,
    current_user: TokenPayload = Depends(require_role(UserRole.COMPANY)),
):
    """
    Remove a recruiter from this company's team.
    Validates the recruiter belongs to this company before deletion.
    """
    repo = RecruiterRepository()
    member = await repo.get_by_id(member_id)

    if not member or member.get("company_id") != current_user.sub:
        raise HTTPException(status_code=404, detail="Team member not found.")

    # Soft Delete Instead of Hard Delete
    update_data = {
        "is_deleted": True,
        "status": "inactive",
        "deleted_at": datetime.now(timezone.utc),
        "deleted_by": current_user.sub,
        "updated_at": datetime.now(timezone.utc)
    }
    
    deleted = await repo.update(member_id, update_data)
    if not deleted:
        raise HTTPException(status_code=404, detail="Team member not found.")
        
    # Deactivate associated user record
    from app.repositories.user_repository import UserRepository
    user_repo = UserRepository()
    user = await user_repo.get_by_email(member.get("email", ""))
    if user:
        await user_repo.update(str(user["_id"]), {"is_active": False})

    company_repo = CompanyRepository()
    await company_repo.update_usage(current_user.sub, "recruiters_used", -1)

    return {"message": "Team member removed successfully.", "id": member_id}


class ReassignRequest(BaseModel):
    new_recruiter_id: str


@router.post("/{member_id}/reassign", summary="Reassign entities to another recruiter")
async def reassign_team_member(
    member_id: str,
    payload: ReassignRequest,
    current_user: TokenPayload = Depends(require_role(UserRole.COMPANY)),
):
    """
    Reassign all campaigns and candidates from `member_id` to `new_recruiter_id`.
    Used during soft deletion to ensure data isn't orphaned.
    """
    repo = RecruiterRepository()
    old_member = await repo.get_by_id(member_id)
    new_member = await repo.get_by_id(payload.new_recruiter_id)

    if not old_member or old_member.get("company_id") != current_user.sub:
        raise HTTPException(status_code=404, detail="Source team member not found.")
        
    if not new_member or new_member.get("company_id") != current_user.sub or new_member.get("is_deleted"):
        raise HTTPException(status_code=400, detail="Target team member is invalid or deleted.")
        
    # Reassign candidates
    from app.repositories.candidate_repository import CandidateRepository
    candidate_repo = CandidateRepository()
    await candidate_repo.collection.update_many(
        {"assigned_recruiter_id": ObjectId(member_id)},
        {"$set": {"assigned_recruiter_id": ObjectId(payload.new_recruiter_id), "updated_at": datetime.now(timezone.utc)}}
    )
    
    # Reassign campaigns (array)
    from app.repositories.campaign_repository import CampaignRepository
    campaign_repo = CampaignRepository()
    
    # First, pull old member from assigned_recruiter_ids
    await campaign_repo.collection.update_many(
        {"assigned_recruiter_ids": ObjectId(member_id)},
        {"$pull": {"assigned_recruiter_ids": ObjectId(member_id)}}
    )
    # Second, push new member to those campaigns (if not already there)
    # In a perfect world, we'd only add if it's not there, but addToSet handles that.
    await campaign_repo.collection.update_many(
        {"assigned_recruiter_ids": {"$exists": True}},
        {"$addToSet": {"assigned_recruiter_ids": ObjectId(payload.new_recruiter_id)}}
    )
    
    return {"message": f"Successfully reassigned data to {new_member.get('name')}"}


# ──────────────────────────────────────────────────────────────────────
# Additional Management Endpoints
# ──────────────────────────────────────────────────────────────────────

@router.post("/{member_id}/reset-password", summary="Reset Password")
async def reset_recruiter_password(
    member_id: str,
    current_user: TokenPayload = Depends(require_role(UserRole.COMPANY))
):
    repo = RecruiterRepository()
    member = await repo.get_by_id(member_id)
    if not member or member.get("company_id") != current_user.sub:
        raise HTTPException(status_code=404, detail="Team member not found.")
        
    import secrets
    import string
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    temp_password = "".join(secrets.choice(alphabet) for _ in range(12))
    
    from app.auth.jwt_handler import hash_password
    hashed_pwd = hash_password(temp_password)
    
    from app.repositories.user_repository import UserRepository
    user_repo = UserRepository()
    user = await user_repo.get_by_email(member.get("email", ""))
    if not user:
        raise HTTPException(status_code=400, detail="Team member has no associated user account")
        
    await user_repo.update(str(user["_id"]), {
        "password_hash": hashed_pwd,
        "must_change_password": True
    })
    
    return {"temporary_password": temp_password, "message": "Password reset successfully"}


@router.post("/{member_id}/suspend", summary="Suspend Team Member")
async def suspend_recruiter(
    member_id: str,
    current_user: TokenPayload = Depends(require_role(UserRole.COMPANY))
):
    """Suspend a recruiter account (disables login)."""
    repo = RecruiterRepository()
    member = await repo.get_by_id(member_id)
    if not member or member.get("company_id") != current_user.sub:
        raise HTTPException(status_code=404, detail="Team member not found.")
    
    await repo.update(member_id, {
        "status": "suspended",
        "updated_at": datetime.now(timezone.utc)
    })
    
    from app.repositories.user_repository import UserRepository
    user_repo = UserRepository()
    user = await user_repo.get_by_email(member.get("email", ""))
    if user:
        await user_repo.update(str(user["_id"]), {"is_active": False})
    
    return {"message": "Team member suspended successfully"}


@router.post("/{member_id}/activate", summary="Activate Team Member")
async def activate_recruiter(
    member_id: str,
    current_user: TokenPayload = Depends(require_role(UserRole.COMPANY))
):
    """Reactivate a suspended recruiter account."""
    repo = RecruiterRepository()
    member = await repo.get_by_id(member_id)
    if not member or member.get("company_id") != current_user.sub:
        raise HTTPException(status_code=404, detail="Team member not found.")
    
    await repo.update(member_id, {
        "status": "active",
        "updated_at": datetime.now(timezone.utc)
    })
    
    from app.repositories.user_repository import UserRepository
    user_repo = UserRepository()
    user = await user_repo.get_by_email(member.get("email", ""))
    if user:
        await user_repo.update(str(user["_id"]), {"is_active": True})
    
    return {"message": "Team member activated successfully"}


@router.post("/{member_id}/force-reset", summary="Force Password Reset")
async def force_password_reset(
    member_id: str,
    current_user: TokenPayload = Depends(require_role(UserRole.COMPANY))
):
    """Force the recruiter to change their password on next login."""
    repo = RecruiterRepository()
    member = await repo.get_by_id(member_id)
    if not member or member.get("company_id") != current_user.sub:
        raise HTTPException(status_code=404, detail="Team member not found.")
    
    from app.repositories.user_repository import UserRepository
    user_repo = UserRepository()
    user = await user_repo.get_by_email(member.get("email", ""))
    if not user:
        raise HTTPException(status_code=400, detail="Team member has no associated user account")
    
    await user_repo.update(str(user["_id"]), {
        "must_change_password": True,
        "refresh_token_hash": None,
        "updated_at": datetime.now(timezone.utc)
    })
    
    return {"message": "Team member will be required to change password on next login"}


@router.get("/{member_id}/campaigns", summary="Get Recruiter Campaigns")
async def get_recruiter_campaigns(
    member_id: str,
    current_user: TokenPayload = Depends(require_role(UserRole.COMPANY))
):
    from app.repositories.campaign_repository import CampaignRepository
    from bson import ObjectId
    
    repo = RecruiterRepository()
    member = await repo.get_by_id(member_id)
    if not member or member.get("company_id") != current_user.sub:
        raise HTTPException(status_code=404, detail="Team member not found.")
        
    campaign_repo = CampaignRepository()
    campaigns = await campaign_repo.get_many({
        "company_id": ObjectId(current_user.sub),
        "assigned_recruiter_ids": ObjectId(member_id)
    })
    
    for c in campaigns:
        c["_id"] = str(c["_id"])
        c["company_id"] = str(c["company_id"])
        c["assigned_recruiter_ids"] = [str(rid) for rid in c.get("assigned_recruiter_ids", [])]
        
    return campaigns


class CampaignAssignRequest2(BaseModel):
    campaign_ids: list[str]


@router.post("/{member_id}/campaigns", summary="Update Recruiter Campaigns")
async def assign_recruiter_campaigns(
    member_id: str,
    payload: CampaignAssignRequest2,
    current_user: TokenPayload = Depends(require_role(UserRole.COMPANY))
):
    from app.repositories.campaign_repository import CampaignRepository
    from bson import ObjectId
    
    repo = RecruiterRepository()
    member = await repo.get_by_id(member_id)
    if not member or member.get("company_id") != current_user.sub:
        raise HTTPException(status_code=404, detail="Team member not found.")
        
    campaign_repo = CampaignRepository()
    
    # Remove this recruiter from all campaigns they were assigned to
    await campaign_repo.collection.update_many(
        {"company_id": ObjectId(current_user.sub), "assigned_recruiter_ids": ObjectId(member_id)},
        {"$pull": {"assigned_recruiter_ids": ObjectId(member_id)}}
    )
    
    # Add recruiter to the selected campaigns
    if payload.campaign_ids:
        object_ids = [ObjectId(cid) for cid in payload.campaign_ids]
        await campaign_repo.collection.update_many(
            {"_id": {"$in": object_ids}, "company_id": ObjectId(current_user.sub)},
            {"$addToSet": {"assigned_recruiter_ids": ObjectId(member_id)}}
        )
        
    return {"message": "Campaigns updated successfully"}


@router.get("/{member_id}/activity", summary="Get Recruiter Activity")
async def get_recruiter_activity(
    member_id: str,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: TokenPayload = Depends(require_role(UserRole.COMPANY))
):
    repo = RecruiterRepository()
    member = await repo.get_by_id(member_id)
    if not member or member.get("company_id") != current_user.sub:
        raise HTTPException(status_code=404, detail="Team member not found.")
        
    from app.repositories.audit_log_repository import AuditLogRepository
    audit_repo = AuditLogRepository()
    
    logs = await audit_repo.get_by_actor(current_user.sub, member_id, limit=limit, skip=offset)
    for log in logs:
        log["id"] = str(log["_id"])
        log.pop("_id", None)
        log["actor_id"] = str(log["actor_id"])
        log["company_id"] = str(log["company_id"])
        
    return logs


@router.get("/{member_id}/candidates", summary="Get Recruiter Candidates")
async def get_recruiter_candidates(
    member_id: str,
    current_user: TokenPayload = Depends(require_role(UserRole.COMPANY))
):
    from app.repositories.candidate_repository import CandidateRepository
    from bson import ObjectId
    
    repo = RecruiterRepository()
    member = await repo.get_by_id(member_id)
    if not member or member.get("company_id") != current_user.sub:
        raise HTTPException(status_code=404, detail="Team member not found.")
        
    candidate_repo = CandidateRepository()
    candidates = await candidate_repo.get_many({
        "company_id": ObjectId(current_user.sub),
        "assigned_recruiter_id": ObjectId(member_id)
    })
    
    for c in candidates:
        c["_id"] = str(c["_id"])
        c["company_id"] = str(c["company_id"])
        c["campaign_id"] = str(c.get("campaign_id")) if c.get("campaign_id") else None
        c["assigned_recruiter_id"] = str(c.get("assigned_recruiter_id")) if c.get("assigned_recruiter_id") else None
        
    return candidates


@router.get("/{member_id}/interviews", summary="Get Recruiter Interviews")
async def get_recruiter_interviews(
    member_id: str,
    current_user: TokenPayload = Depends(require_role(UserRole.COMPANY))
):
    from app.repositories.interview_session_repository import InterviewSessionRepository
    from app.repositories.candidate_repository import CandidateRepository
    from bson import ObjectId
    
    repo = RecruiterRepository()
    member = await repo.get_by_id(member_id)
    if not member or member.get("company_id") != current_user.sub:
        raise HTTPException(status_code=404, detail="Team member not found.")
        
    candidate_repo = CandidateRepository()
    candidates = await candidate_repo.get_many({
        "company_id": ObjectId(current_user.sub),
        "assigned_recruiter_id": ObjectId(member_id)
    })
    
    candidate_ids = [c["_id"] for c in candidates]
    
    if not candidate_ids:
        return []
        
    session_repo = InterviewSessionRepository()
    sessions = await session_repo.get_many({
        "company_id": ObjectId(current_user.sub),
        "candidate_id": {"$in": candidate_ids}
    })
    
    for s in sessions:
        s["_id"] = str(s["_id"])
        s["company_id"] = str(s["company_id"])
        s["candidate_id"] = str(s["candidate_id"])
        s["campaign_id"] = str(s.get("campaign_id")) if s.get("campaign_id") else None
        
    return sessions
