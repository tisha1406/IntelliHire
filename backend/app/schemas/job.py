from typing import Optional, Literal
from pydantic import BaseModel, Field

class JobCreateRequest(BaseModel):
    title: str
    department: str
    location: str
    employment_type: str
    salary_scale: Optional[str] = ""
    status: Literal["Active", "Closed", "Draft"] = "Active"

class JobUpdateRequest(BaseModel):
    title: Optional[str] = None
    department: Optional[str] = None
    location: Optional[str] = None
    employment_type: Optional[str] = None
    salary_scale: Optional[str] = None
    status: Optional[Literal["Active", "Closed", "Draft"]] = None

class JobResponse(BaseModel):
    job_id: str
    title: str
    department: str
    location: str
    employment_type: str
    salary_scale: str
    status: str
    applicants: int
    created_at: str

class JobUpdateResponse(BaseModel):
    updated_fields: list[str]
