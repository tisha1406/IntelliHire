from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class CompanyCreateRequest(BaseModel):
    name: str = Field(..., min_length=2)
    contact_email: EmailStr

    allowed_languages: list[str]
    allowed_voices: list[str]
    allowed_strategies: list[str]
    allowed_interview_modes: list[str]
    allowed_llm_tiers: list[str]

    max_campaigns: int = Field(..., gt=0)


class CompanyUpdateRequest(BaseModel):
    name: Optional[str] = None
    contact_email: Optional[EmailStr] = None

    allowed_languages: Optional[list[str]] = None
    allowed_voices: Optional[list[str]] = None
    allowed_strategies: Optional[list[str]] = None
    allowed_interview_modes: Optional[list[str]] = None
    allowed_llm_tiers: Optional[list[str]] = None

    max_campaigns: Optional[int] = Field(default=None, gt=0)


class CompanyCreateResponse(BaseModel):
    company_id: str


class CompanyUpdateResponse(BaseModel):
    updated_fields: list[str]


class CompanyResponse(BaseModel):
    id: str
    name: str
    contact_email: EmailStr

    allowed_languages: list[str]
    allowed_voices: list[str]
    allowed_strategies: list[str]
    allowed_interview_modes: list[str]
    allowed_llm_tiers: list[str]

    max_campaigns: int
    status: str

class StrategyCreateRequest(BaseModel):
    strategy_id: str
    display_name: str
    description: str
    prompt_template_ref: str
    enabled: bool = True


class StrategyUpdateRequest(BaseModel):
    enabled: Optional[bool] = None


class StrategyResponse(BaseModel):
    strategy_id: str


class StrategyUpdateResponse(BaseModel):
    updated_fields: list[str]

class DifficultyPolicyRequest(BaseModel):
    start: str
    progression: str


class InterviewModeCreateRequest(BaseModel):
    display_name: str
    internal_strategy: str
    max_follow_ups_per_topic: int
    topic_saturation_threshold: float
    completion_confidence_threshold: float
    difficulty_policy: DifficultyPolicyRequest
    behavioral_templates_enabled: bool
    is_default: bool
    enabled: bool


class InterviewModeUpdateRequest(BaseModel):
    display_name: Optional[str] = None
    internal_strategy: Optional[str] = None
    max_follow_ups_per_topic: Optional[int] = None
    topic_saturation_threshold: Optional[float] = None
    completion_confidence_threshold: Optional[float] = None
    difficulty_policy: Optional[DifficultyPolicyRequest] = None
    behavioral_templates_enabled: Optional[bool] = None
    is_default: Optional[bool] = None
    enabled: Optional[bool] = None


class InterviewModeCreateResponse(BaseModel):
    interview_mode_id: str


class InterviewModeUpdateResponse(BaseModel):
    updated_fields: list[str]
