from pydantic import BaseModel, EmailStr


class CandidateCreateRequest(BaseModel):
    name: str
    email: EmailStr
    campaign_invite_token: str


class CandidateCreateResponse(BaseModel):
    candidate_id: str
    jwt: str