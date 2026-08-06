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

    deleted = await repo.delete(member_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Team member not found.")

    company_repo = CompanyRepository()
    await company_repo.update_usage(current_user.sub, "recruiters_used", -1)

    return {"message": "Team member removed successfully.", "id": member_id}
