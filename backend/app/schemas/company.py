from typing import List, Optional, Union, Dict
from pydantic import BaseModel, Field, field_validator

from app.ai_interview.core.enums import InterviewType, RequirementCriticality, DifficultyLevel
from app.ai_interview.schemas.strategy import MixedComposition

ALLOWED_VOICES = {"shubh", "simran", "rohan", "ishita", "sunny"}

class InterviewSettingsRequest(BaseModel):
    duration: int
    strictness: str
    type: str


class CampaignRequirement(BaseModel):
    skill: str
    criticality: RequirementCriticality = RequirementCriticality.REQUIRED

class CampaignQuestionBudget(BaseModel):
    target_questions: Optional[int] = None


class CampaignCreateRequest(BaseModel):
    company_id: Optional[str] = None

    name: str
    department: str
    location: str
    deadline: str
    salary: str
    description: str
    employment_type: str

    requirements: List[Union[str, CampaignRequirement]]

    interview_settings: InterviewSettingsRequest
    
    assigned_recruiter_ids: List[str] = Field(default_factory=list)

    # Official Strategy Fields
    strategy_id: Optional[str] = None
    interview_type: Optional[InterviewType] = None
    mixed_composition: Optional[MixedComposition] = None
    budget_override: Optional[CampaignQuestionBudget] = None
    difficulty_band: Optional[DifficultyLevel] = None
    
    # Existing Voice/Language options passed during campaign creation
    language: Optional[str] = None
    voice_id: Optional[str] = None

    @field_validator("voice_id")
    @classmethod
    def validate_voice_id(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v.lower() not in ALLOWED_VOICES:
            raise ValueError(f"Voice '{v}' is not allowed. Must be one of: {', '.join(ALLOWED_VOICES)}")
        return v


class CampaignUpdateRequest(BaseModel):
    name: Optional[str] = None
    department: Optional[str] = None
    location: Optional[str] = None
    deadline: Optional[str] = None
    salary: Optional[str] = None
    description: Optional[str] = None
    employment_type: Optional[str] = None

    requirements: Optional[List[Union[str, CampaignRequirement]]] = None

    interview_settings: Optional[InterviewSettingsRequest] = None

    status: Optional[str] = None
    
    assigned_recruiter_ids: Optional[List[str]] = None

    strategy_id: Optional[str] = None
    interview_type: Optional[InterviewType] = None
    mixed_composition: Optional[MixedComposition] = None
    budget_override: Optional[CampaignQuestionBudget] = None
    difficulty_band: Optional[DifficultyLevel] = None
    language: Optional[str] = None
    voice_id: Optional[str] = None
    
    @field_validator("voice_id")
    @classmethod
    def validate_voice_id(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v.lower() not in ALLOWED_VOICES:
            raise ValueError(f"Voice '{v}' is not allowed. Must be one of: {', '.join(ALLOWED_VOICES)}")
        return v
class CampaignResponse(BaseModel):
    campaign_id: str
    # Non-blocking configuration warnings (e.g. R-13's
    # max_questions_per_topic * critical_topic_count > max_questions check).
    # The campaign is still created/updated when warnings are present — this
    # is a safety-net notice, never a validation failure.
    warnings: List[str] = Field(default_factory=list)


class CampaignUpdateResponse(BaseModel):
    updated_fields: List[str]
    warnings: List[str] = Field(default_factory=list)


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