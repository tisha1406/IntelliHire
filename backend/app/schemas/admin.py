from typing import Optional, List, Dict, Any

from pydantic import BaseModel, EmailStr, Field

class CompanyGeneralSchema(BaseModel):
    name: str = Field(..., min_length=2)
    contact_email: EmailStr
    industry: Optional[str] = None
    size: Optional[str] = None
    website: Optional[str] = None
    phone: Optional[str] = None
    country: Optional[str] = None
    timezone: Optional[str] = None
    currency: Optional[str] = None
    address: Optional[str] = None
    contact_person: Optional[str] = None
    tax_id: Optional[str] = None
    notes: Optional[str] = None
    logo_url: Optional[str] = None

class CompanySubscriptionSchema(BaseModel):
    plan: str = "Enterprise"
    status: str = "active"
    billing_cycle: str = "annual"
    expiry_date: Optional[str] = None
    seat_count: int = 5

class CompanyLimitsSchema(BaseModel):
    max_recruiters: int = 5
    max_candidates: int = 500
    max_campaigns: int = 10
    monthly_interviews: int = 100
    concurrent_interviews: int = 5
    storage_limit_gb: float = 10.0
    api_requests_per_month: int = 10000
    ai_credits: int = 1000
    resume_uploads: int = 5000

class CompanySecuritySchema(BaseModel):
    login_enabled: bool = True
    mfa_required: bool = False
    password_policy: str = "standard"
    session_timeout_minutes: int = 60
    jwt_lifetime_hours: int = 24
    refresh_token_lifetime_days: int = 7
    sso_enabled: bool = False
    allowed_domains: List[str] = Field(default_factory=list)
    ip_whitelist: List[str] = Field(default_factory=list)
    concurrent_sessions_allowed: int = 3
    remember_me_allowed: bool = True
    login_attempts_before_lockout: int = 5

class CompanyCreateRequest(BaseModel):
    general: CompanyGeneralSchema
    subscription: CompanySubscriptionSchema
    limits: CompanyLimitsSchema
    security: CompanySecuritySchema

    features: Dict[str, bool] = Field(default_factory=dict)
    
    allowed_languages: List[str] = Field(default_factory=list)
    allowed_voices: List[str] = Field(default_factory=list)
    allowed_strategies: List[str] = Field(default_factory=list)
    allowed_interview_modes: List[str] = Field(default_factory=list)
    allowed_llm_tiers: List[str] = Field(default_factory=list)

class CompanyUpdateRequest(BaseModel):
    general: Optional[CompanyGeneralSchema] = None
    subscription: Optional[CompanySubscriptionSchema] = None
    limits: Optional[CompanyLimitsSchema] = None
    security: Optional[CompanySecuritySchema] = None
    features: Optional[Dict[str, bool]] = None
    
    allowed_languages: Optional[List[str]] = None
    allowed_voices: Optional[List[str]] = None
    allowed_strategies: Optional[List[str]] = None
    allowed_interview_modes: Optional[List[str]] = None
    allowed_llm_tiers: Optional[List[str]] = None

class CompanyCreateResponse(BaseModel):
    company_id: str
    username: str
    temporary_password: str

class CompanyUpdateResponse(BaseModel):
    updated_fields: list[str]

class CompanyResponse(BaseModel):
    id: str
    general: CompanyGeneralSchema
    subscription: CompanySubscriptionSchema
    limits: CompanyLimitsSchema
    security: CompanySecuritySchema
    features: Dict[str, bool]
    
    allowed_languages: List[str] = Field(default_factory=list)
    allowed_voices: List[str] = Field(default_factory=list)
    allowed_strategies: List[str] = Field(default_factory=list)
    allowed_interview_modes: List[str] = Field(default_factory=list)
    allowed_llm_tiers: List[str] = Field(default_factory=list)
    
    created_at: str = "2026-01-01T00:00:00Z"
    updated_at: str = "2026-01-01T00:00:00Z"
    deleted_at: Optional[str] = None

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
