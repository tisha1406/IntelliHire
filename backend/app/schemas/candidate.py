from typing import List, Optional

from pydantic import BaseModel, EmailStr


# ==========================================
# Candidate Registration
# ==========================================

class CandidateCreateRequest(BaseModel):
    name: str
    email: EmailStr
    campaign_invite_token: str
    password: str


class CandidateCreateResponse(BaseModel):
    candidate_id: str
    jwt: str


# ==========================================
# Company Panel
# ==========================================

class CandidateUpdateRequest(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    education: Optional[str] = None
    experience: Optional[str] = None
    skills: Optional[List[str]] = None


class CandidateResponse(BaseModel):
    id: str
    name: str
    email: EmailStr
    phone: Optional[str] = None
    education: Optional[str] = None
    experience: Optional[str] = None
    skills: List[str] = []
    ai_match: Optional[int] = 0
    resume_score: Optional[int] = 0
    interview_score: Optional[int] = 0
    current_stage: Optional[str] = "Applied"
    status: Optional[str] = "Pending"