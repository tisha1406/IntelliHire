from datetime import UTC, datetime
from typing import List, Optional, Literal

from bson import ObjectId
from pydantic import BaseModel, ConfigDict, Field


# ==========================================================
# MongoDB ObjectId Support
# ==========================================================

class PyObjectId(ObjectId):
    @classmethod
    def __get_pydantic_core_schema__(cls, source_type, handler):
        from pydantic_core import core_schema

        return core_schema.no_info_after_validator_function(
            cls.validate,
            core_schema.str_schema(),
        )

    @classmethod
    def validate(cls, value):
        if not ObjectId.is_valid(value):
            raise ValueError("Invalid ObjectId")
        return ObjectId(value)


# ==========================================================
# Base Mongo Model
# ==========================================================

class MongoBaseModel(BaseModel):
    id: Optional[PyObjectId] = Field(default=None, alias="_id")

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str},
    )


# ==========================================================
# Users Collection
# ==========================================================

class User(MongoBaseModel):
    role: Literal[
        "admin",
        "company",
        "recruiter",
        "candidate",
    ]

    email: str

    password_hash: str

    company_id: Optional[PyObjectId] = None

    candidate_id: Optional[PyObjectId] = None

    recruiter_id: Optional[PyObjectId] = None

    is_active: bool = True

    must_change_password: bool = False

    password_reset_required: bool = False

    created_by: Optional[PyObjectId] = None

    last_login: Optional[datetime] = None

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC)
    )

    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC)
    )


# ==========================================================
# Company Branding
# ==========================================================

class Branding(BaseModel):
    logo_url: Optional[str] = None
    accent_color: str = "#4f46e5"


# ==========================================================
# Company Configuration Models
# ==========================================================

class CompanyGeneral(BaseModel):
    name: str
    contact_email: str
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

class CompanySubscription(BaseModel):
    plan: str = "Enterprise"
    status: Literal["active", "suspended", "trial", "cancelled"] = "active"
    billing_cycle: Literal["monthly", "annual"] = "annual"
    expiry_date: Optional[str] = None
    seat_count: int = 5

class CompanyLimits(BaseModel):
    max_recruiters: int = 5
    max_candidates: int = 500
    max_campaigns: int = 10
    monthly_interviews: int = 100
    concurrent_interviews: int = 5
    storage_limit_gb: float = 10.0
    api_requests_per_month: int = 10000
    ai_credits: int = 1000
    resume_uploads: int = 5000

class CompanySecurity(BaseModel):
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

# ==========================================================
# Companies Collection
# ==========================================================

class CompanyFeatures(BaseModel):
    ai_reports: bool = True
    practice_interview: bool = True
    official_interview: bool = True
    recruiter_management: bool = True
    analytics: bool = True
    reports: bool = True
    exports: bool = True
    resume_analysis: bool = True
    multilingual_support: bool = True

class Company(MongoBaseModel):
    company_name: str = ""
    general: CompanyGeneral
    subscription: CompanySubscription
    limits: CompanyLimits
    security: CompanySecurity

    # Arrays of ObjectIDs or strings identifying configured resources
    allowed_languages: List[str] = Field(default_factory=list)
    allowed_voices: List[str] = Field(default_factory=list)
    allowed_strategies: List[str] = Field(default_factory=list)
    allowed_interview_modes: List[str] = Field(default_factory=list)
    allowed_llm_tiers: List[str] = Field(default_factory=list)
    
    # Object storing boolean toggles for features
    features: CompanyFeatures = Field(
    default_factory=CompanyFeatures
    )

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC)
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC)
    )

# ==========================================================
# Strategy Definitions
# ==========================================================

class Strategy(MongoBaseModel):

    strategy_id: str

    display_name: str

    description: str

    prompt_template_ref: str

    enabled: bool = True

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC)
    )

    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC)
    )

# ==========================================================
# Interview Campaign
# ==========================================================

class VoiceConfig(BaseModel):
    voice_id: str
    language: str
    accent: str


class InterviewCampaign(MongoBaseModel):
    company_id: PyObjectId
    created_by: Optional[PyObjectId] = None

    name: str

    role_target: str

    interview_type: Literal[
        "technical",
        "hr",
        "behavioral",
        "mixed",
    ]

    voice_config: VoiceConfig

    interview_mode: str

    delegate_language_choice_to_candidate: bool

    delegate_domain_choice_to_candidate: bool

    allowed_candidate_languages: List[str]

    status: Literal["active", "closed"]

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC)
    )

    updated_at: datetime = Field(
    default_factory=lambda: datetime.now(UTC)
    )


# ==========================================================
# Interview Mode Definition
# ==========================================================

class DifficultyPolicy(BaseModel):
    start: str
    progression: str


class InterviewModeDefinition(MongoBaseModel):
    display_name: str

    internal_strategy: str

    max_follow_ups_per_topic: int

    topic_saturation_threshold: float

    completion_confidence_threshold: float

    difficulty_policy: DifficultyPolicy

    behavioral_templates_enabled: bool

    is_default: bool

    enabled: bool

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC)
    )

    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC)
    )

# ==========================================================
# Candidate Resume Profile Models
# ==========================================================

class Experience(BaseModel):
    title: str
    org: str
    description: str
    duration: str


class Education(BaseModel):
    degree: str
    institution: str
    year: str


class Project(BaseModel):
    name: str
    description: str
    technologies: List[str] = Field(default_factory=list)


class ResumeProfile(BaseModel):
    candidate_name: str

    target_role: str

    experience: List[Experience] = Field(default_factory=list)

    education: List[Education] = Field(default_factory=list)

    skills: List[str] = Field(default_factory=list)

    projects: List[Project] = Field(default_factory=list)

    certifications: List[str] = Field(default_factory=list)

    strengths: List[str] = Field(default_factory=list)

    technologies: List[str] = Field(default_factory=list)

    domains: List[str] = Field(default_factory=list)

    potential_interview_topics: List[str] = Field(default_factory=list)


# ==========================================================
# Candidates Collection
# ==========================================================

class Candidate(MongoBaseModel):
    campaign_id: PyObjectId

    company_id: PyObjectId

    name: str

    email: str

    experience_level: str

    target_role: str

    resume_profile: ResumeProfile

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC)
    )

# ==========================================================
# Interview Session Models
# ==========================================================

class ComplexityScores(BaseModel):
    experience: float
    skills: float
    projects: float


class QuestionBudget(BaseModel):
    min_questions: int
    max_questions: int
    complexity_scores: ComplexityScores


class InterviewBlueprintItem(BaseModel):
    topic_name: str
    section: str
    importance: Literal[
        "mandatory",
        "high",
        "medium",
        "low",
    ]
    priority_rank: int
    target_difficulty: Literal[
        "easy",
        "medium",
        "hard",
    ]
    estimated_coverage: Literal[
        "low",
        "medium",
        "high",
    ]


class TopicCoverage(BaseModel):
    status: str
    questions_asked: int
    follow_ups_asked: int
    topic_confidence_score: float
    last_score: float


class InterviewState(BaseModel):

    current_question: str

    current_topic: str

    last_three_questions: List[str] = Field(default_factory=list)

    last_three_answers: List[str] = Field(default_factory=list)

    difficulty: str

    weak_areas: List[str] = Field(default_factory=list)

    strong_areas: List[str] = Field(default_factory=list)

    score_history: List[float] = Field(default_factory=list)

    topics_remaining: List[str] = Field(default_factory=list)

    topics_covered: List[str] = Field(default_factory=list)

    interview_blueprint: List[InterviewBlueprintItem] = Field(
        default_factory=list
    )

    topic_coverage_map: dict[str, TopicCoverage] = Field(
        default_factory=dict
    )

    current_topic_follow_up_count: int = 0

    overall_coverage_percentage: float = 0.0

    overall_interview_confidence: float = 0.0

    questions_asked_total: int = 0

    mandatory_topics_completed: bool = False

    interview_phase: str

    exploitation_attempt_count: int = 0


class Evaluation(BaseModel):

    technical_score: float

    communication_score: float

    completeness_score: float

    logical_flow_score: float

    resume_consistency_score: float

    project_explanation_score: float

    professionalism_score: float

    response_quality_score: float

    topic: str

    readiness_score: float

    suggests_follow_up: bool

    follow_up_reason: Optional[str] = None


class Turn(BaseModel):

    turn_number: int

    question: str

    answer_transcript: str

    response_time_seconds: float

    evaluation: Evaluation

    was_follow_up: bool = False

    was_blocked_by_guardrail: bool = False

    calibrate_hold_triggered: bool = False

    cheating_risk_detected: bool = False


class InterviewSession(MongoBaseModel):

    strategy_id: Optional[str] = None

    llm_model: Optional[str] = None

    voice_model: Optional[str] = None

    company_id: PyObjectId

    campaign_id: PyObjectId

    candidate_id: PyObjectId

    language: str

    interview_mode: str

    status: Literal[
        "in_progress",
        "completed",
    ]

    question_budget: QuestionBudget

    interview_state: InterviewState

    turns: List[Turn] = Field(default_factory=list)

    last_disconnected_at: Optional[datetime] = None

    incomplete_coverage: bool = False

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC)
    )

    completed_at: Optional[datetime] = None

    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC)
    )

# ==========================================================
# Interview Report Models
# ==========================================================

class ResumeMatchAnalysis(BaseModel):
    matched_skills: List[str] = Field(default_factory=list)
    gap_skills: List[str] = Field(default_factory=list)
    consistency_notes: str


class InterviewRiskAssessment(BaseModel):
    risks: List[str] = Field(default_factory=list)
    severity: Literal[
        "low",
        "medium",
        "high",
    ]


class TopicSelectionExplanation(BaseModel):
    topic: str
    reason: str


class DifficultyChangeExplanation(BaseModel):
    turn: int
    change: str
    reason: str


class FollowUpExplanation(BaseModel):
    turn: int
    reason: str


class CompletionExplanation(BaseModel):
    reason: str


class ReadinessScoreExplanation(BaseModel):
    formula_summary: str
    score: float


class Explainability(BaseModel):

    topic_selection_explanations: List[
        TopicSelectionExplanation
    ] = Field(default_factory=list)

    difficulty_change_explanations: List[
        DifficultyChangeExplanation
    ] = Field(default_factory=list)

    follow_up_explanations: List[
        FollowUpExplanation
    ] = Field(default_factory=list)

    completion_explanation: CompletionExplanation

    readiness_score_explanation: ReadinessScoreExplanation


class InterviewReport(MongoBaseModel):

    session_id: PyObjectId

    company_id: PyObjectId

    campaign_id: PyObjectId

    overall_score: int

    interview_readiness_score: float

    resume_match_analysis: ResumeMatchAnalysis

    topic_wise_scores: dict[str, int] = Field(default_factory=dict)

    technical_skills_assessment: str

    communication_assessment: str

    interview_risk_assessment: InterviewRiskAssessment

    strengths: str

    weaknesses: str

    improvement_plan: str

    learning_resources: List[str] = Field(default_factory=list)

    recruiter_summary: str

    explainability: Explainability

    generated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC)
    )

    updated_at: datetime = Field(
    default_factory=lambda: datetime.now(UTC)
    )


# ==========================================================
# Validator Logs
# ==========================================================

class ValidatorLog(MongoBaseModel):

    session_id: PyObjectId

    turn_number: int

    attempt: int

    passed: bool

    failed_rules: List[str] = Field(default_factory=list)

    candidate_question_text: str

    logged_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC)
    )

    updated_at: datetime = Field(
    default_factory=lambda: datetime.now(UTC)
    )


# ==========================================================
# Candidate Workflow State Machine
# ==========================================================

class WorkflowStep(BaseModel):
    key: str
    label: str
    status: Literal["locked", "available", "in_progress", "completed"]
    completed_at: Optional[datetime] = None


class CandidateWorkflow(MongoBaseModel):
    candidate_id: PyObjectId
    user_id: PyObjectId
    company_id: PyObjectId
    campaign_id: PyObjectId

    # High-level lifecycle stage
    stage: Literal[
        "INVITATION_PENDING",
        "ACCOUNT_ACTIVATED",
        "PROFILE_INCOMPLETE",
        "RESUME_UPLOAD_REQUIRED",
        "RESUME_PROCESSING",
        "RESUME_ANALYSIS_COMPLETE",
        "PRACTICE_AVAILABLE",
        "OFFICIAL_INTERVIEW_READY",
        "INTERVIEW_IN_PROGRESS",
        "AI_EVALUATION_RUNNING",
        "REPORT_AVAILABLE",
        "COMPLETED",
    ] = "RESUME_UPLOAD_REQUIRED"

    # Next action for the dashboard card
    next_action: Literal[
        "UPLOAD_RESUME",
        "WAITING_ANALYSIS",
        "PRACTICE",
        "SYSTEM_CHECK",
        "OFFICIAL_INTERVIEW",
        "WAITING_REPORT",
        "VIEW_REPORT",
        "COMPLETED",
    ] = "UPLOAD_RESUME"

    # Individual step booleans
    resume_uploaded: bool = False
    resume_processing: bool = False
    resume_analysed: bool = False
    practice_started: bool = False
    practice_completed: bool = False
    system_check_completed: bool = False
    official_started: bool = False
    official_completed: bool = False
    report_ready: bool = False

    # Timestamps
    resume_uploaded_at: Optional[datetime] = None
    resume_analysed_at: Optional[datetime] = None
    practice_started_at: Optional[datetime] = None
    practice_completed_at: Optional[datetime] = None
    official_started_at: Optional[datetime] = None
    official_completed_at: Optional[datetime] = None

    # Computed readiness score (0-100)
    readiness_score: int = 0

    # Ordered timeline steps for the frontend
    steps: List[WorkflowStep] = Field(default_factory=list)

    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


# ==========================================================
# Resume Analysis (persisted structured profile)
# ==========================================================

class RadarDataPoint(BaseModel):
    subject: str
    A: float
    fullMark: float = 100.0


class ResumeAnalysis(MongoBaseModel):
    candidate_id: PyObjectId
    company_id: PyObjectId
    campaign_id: PyObjectId
    version: int = 1

    # Scores
    overall_score: int = 0
    ats_score: int = 0
    role_match: int = 0
    completeness: int = 0

    # Skills
    technical_skills: List[str] = Field(default_factory=list)
    soft_skills: List[str] = Field(default_factory=list)
    missing_skills: List[str] = Field(default_factory=list)
    certifications: List[str] = Field(default_factory=list)
    languages_known: List[str] = Field(default_factory=list)

    # Metrics
    radar_data: List[RadarDataPoint] = Field(default_factory=list)
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)

    # ATS tips
    improve_ats: str = ""
    missing_keywords: List[str] = Field(default_factory=list)
    grammar_score: int = 0
    formatting_score: int = 0

    # Processing timeline
    timeline: List[dict] = Field(default_factory=list)

    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


# ==========================================================
# Candidate Notifications
# ==========================================================

class CandidateNotification(MongoBaseModel):
    candidate_id: PyObjectId
    type: Literal["system", "resume", "interview", "report", "reminder"]
    title: str
    message: str
    read: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


# ==========================================================
# Support Tickets
# ==========================================================

class SupportTicket(MongoBaseModel):
    candidate_id: PyObjectId
    company_id: PyObjectId
    subject: str
    message: str
    status: Literal["open", "in_progress", "resolved", "closed"] = "open"
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


# ==========================================================
# Candidate Settings
# ==========================================================

class CandidateSettings(MongoBaseModel):
    candidate_id: PyObjectId

    # Preferences
    high_contrast: bool = False
    reduced_motion: bool = False
    sidebar_auto_collapse: bool = True

    # Notifications
    interview_reminders: bool = True
    company_updates: bool = True
    result_notifications: bool = True

    # Language
    portal_language: str = "English"
    live_subtitles: bool = True

    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


# ==========================================================
# Activity Log
# ==========================================================

class ActivityLogEntry(MongoBaseModel):
    candidate_id: PyObjectId
    event: str   # e.g. "LOGIN", "RESUME_UPLOADED", "PRACTICE_STARTED"
    description: str
    metadata: dict = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


# ==========================================================
# Candidate Invitation
# ==========================================================

class CandidateInvitation(MongoBaseModel):
    token: str          # Secure random token
    candidate_id: PyObjectId
    user_id: Optional[PyObjectId] = None
    company_id: PyObjectId
    campaign_id: PyObjectId
    email: str
    name: str
    expires_at: datetime
    used: bool = False
    used_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    invited_by: Optional[PyObjectId] = None

# ==========================================================
# Job Openings Collection
# ==========================================================

class JobOpening(MongoBaseModel):

    company_id: PyObjectId

    title: str

    department: str

    location: str

    employment_type: str

    salary_min: Optional[int] = None

    salary_max: Optional[int] = None

    currency: str = "INR"

    status: Literal[
        "Active",
        "Closed",
        "Draft",
    ] = "Draft"

    applicants: int = 0

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC)
    )

    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC)
    )

# ==========================================================
# Company Reports
# ==========================================================

class CompanyReport(MongoBaseModel):
    company_id: Optional[PyObjectId] = None

    name: str

    type: str

    generated_by: str = "System Admin"

    generated_at: datetime = Field(
    default_factory=lambda: datetime.now(UTC)
    )

    status: Literal[
        "Ready",
        "Processing",
        "Failed",
    ] = "Ready"

    size: str = "1.5 MB"

    format: Literal[
        "PDF",
        "Excel",
        "CSV",
    ] = "PDF"

    download_count: int = 0

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC)
    )

    updated_at: datetime = Field(
    default_factory=lambda: datetime.now(UTC)
    )

# ==========================================================
# Company Exports
# ==========================================================

class CompanyExport(MongoBaseModel):
    company_id: Optional[PyObjectId] = None

    title: str

    type: str

    format: str

    record_count: int = 0

    status: Literal[
        "Completed",
        "Processing",
        "Failed",
    ] = "Completed"

    size: str = "500 KB"

    file_name: str

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC)
    )

    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC)
    )