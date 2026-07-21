from pydantic import BaseModel


class ResumeProfileResponse(BaseModel):
    candidate_name: str
    email: str
    skills: list[str]
    education: list[str]
    experience: list[str]