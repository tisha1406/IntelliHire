from datetime import datetime
from typing import Optional, List

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.repositories.user_repository import UserRepository

router = APIRouter(prefix="/company/team", tags=["Company Team"])

user_repo = UserRepository()

INITIAL_TEAM = [
    {"name": "Sarah Jenkins", "designation": "Director of Talent Acquisition", "department": "Human Resources", "email": "sarah.jenkins@intellihire.ai", "phone": "+1 (555) 101-2020", "role": "Admin", "status": "Active"},
    {"name": "Dev Patel", "designation": "Lead AI Technical Recruiter", "department": "Recruitment", "email": "dev.patel@intellihire.ai", "phone": "+1 (555) 101-2021", "role": "Recruiter", "status": "Active"},
    {"name": "Anna Kovac", "designation": "Design & Product Recruiter", "department": "Recruitment", "email": "anna.kovac@intellihire.ai", "phone": "+1 (555) 101-2022", "role": "Recruiter", "status": "Active"},
    {"name": "Marcus Vance", "designation": "Sales & Growth Hiring Partner", "department": "Recruitment", "email": "marcus.vance@intellihire.ai", "phone": "+1 (555) 101-2023", "role": "Recruiter", "status": "Active"},
    {"name": "Elena Rostova", "designation": "Senior Engineering Recruiter", "department": "Recruitment", "email": "elena.rostova@intellihire.ai", "phone": "+1 (555) 101-2024", "role": "Recruiter", "status": "Active"},
    {"name": "Alex Mercer", "designation": "Head of Engineering", "department": "Engineering", "email": "alex.mercer@intellihire.ai", "phone": "+1 (555) 101-2025", "role": "Hiring Manager", "status": "Active"},
    {"name": "Priya Nair", "designation": "VP of Product", "department": "Product", "email": "priya.nair@intellihire.ai", "phone": "+1 (555) 101-2026", "role": "Hiring Manager", "status": "Active"},
]


class TeamMemberResponse(BaseModel):
    id: str
    name: str
    designation: str
    department: str
    email: str
    phone: Optional[str] = ""
    role: str
    status: str


class InviteMemberRequest(BaseModel):
    name: str
    email: str
    role: str


async def seed_team_if_empty():
    count = await user_repo.count({"source": "team_member"})
    if count == 0:
        for m in INITIAL_TEAM:
            doc = {
                **m,
                "source": "team_member",
                "created_at": datetime.utcnow()
            }
            await user_repo.create(doc)


@router.get("", response_model=List[TeamMemberResponse], summary="Get Team Members")
async def get_team(
    search: Optional[str] = Query(None),
    role: Optional[str] = Query(None)
):
    """
    Get all team members from MongoDB. Seeds initial data if empty.
    """
    await seed_team_if_empty()
    members = await user_repo.get_many({"source": "team_member"}, limit=200)

    results = []
    for m in members:
        item = TeamMemberResponse(
            id=str(m["_id"]),
            name=m.get("name", "Unknown"),
            designation=m.get("designation", ""),
            department=m.get("department", ""),
            email=m.get("email", ""),
            phone=m.get("phone", ""),
            role=m.get("role", "Recruiter"),
            status=m.get("status", "Active"),
        )

        if search and search.lower() not in (
            item.name.lower() + item.designation.lower() + item.department.lower()
        ):
            continue
        if role and role.lower() != item.role.lower():
            continue

        results.append(item)

    return results


@router.post("", response_model=TeamMemberResponse, summary="Invite New Team Member")
async def invite_team_member(payload: InviteMemberRequest):
    """
    Add a new team member / recruiter to the company.
    """
    existing = await user_repo.get_by_email(payload.email)
    if existing and existing.get("source") == "team_member":
        raise HTTPException(status_code=409, detail="A team member with this email already exists.")

    doc = {
        "name": payload.name,
        "email": payload.email,
        "role": payload.role,
        "designation": payload.role,
        "department": "Recruitment" if payload.role == "Recruiter" else "Management",
        "phone": "",
        "status": "Active",
        "source": "team_member",
        "created_at": datetime.utcnow()
    }

    inserted_id = await user_repo.create(doc)

    return TeamMemberResponse(
        id=inserted_id,
        name=doc["name"],
        designation=doc["designation"],
        department=doc["department"],
        email=doc["email"],
        phone=doc["phone"],
        role=doc["role"],
        status=doc["status"],
    )


@router.delete("/{member_id}", summary="Remove Team Member")
async def remove_team_member(member_id: str):
    """
    Remove a team member from MongoDB.
    """
    deleted = await user_repo.delete(member_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Team member not found.")
    return {"message": "Team member removed successfully.", "id": member_id}
