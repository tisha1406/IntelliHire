from typing import List, Optional

from pydantic import BaseModel


class InterviewSettingsRequest(BaseModel):
    duration: int
    strictness: str
    type: str


class CampaignCreateRequest(BaseModel):
    company_id: Optional[str] = None

    name: str
    department: str
    location: str
    deadline: str
    salary: str
    description: str
    employment_type: str

    requirements: List[str]

    interview_settings: InterviewSettingsRequest


class CampaignUpdateRequest(BaseModel):
    name: Optional[str] = None
    department: Optional[str] = None
    location: Optional[str] = None
    deadline: Optional[str] = None
    salary: Optional[str] = None
    description: Optional[str] = None
    employment_type: Optional[str] = None

    requirements: Optional[List[str]] = None

    interview_settings: Optional[InterviewSettingsRequest] = None

    status: Optional[str] = None


class CampaignResponse(BaseModel):
    campaign_id: str


class CampaignUpdateResponse(BaseModel):
    updated_fields: List[str]


# ── Reports & Exports Schemas ─────────────────────────────────────────────
class ReportCreateRequest(BaseModel):
    type: str
    period: Optional[str] = "last_month"
    format: Optional[str] = "PDF"
    name: Optional[str] = None


class ReportResponse(BaseModel):
    id: str
    name: str
    type: str
    generatedBy: str
    date: str
    status: str
    size: str
    format: str
    downloadCount: int = 0


class ExportCreateRequest(BaseModel):
    type: str
    format: str


class ExportResponse(BaseModel):
    id: str
    title: str
    format: str
    records: str
    status: str
    created_at: str
    size: str
    file_name: str


class ReportStatisticsResponse(BaseModel):
    total_candidates: int
    total_interviews: int
    selections: int
    active_campaigns: int
    avg_ai_score: float
    avg_time_to_hire_days: int