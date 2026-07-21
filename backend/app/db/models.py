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
    role: Literal["admin", "company"]
    email: str
    password_hash: str
    company_id: Optional[PyObjectId] = None
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC)
    )


# ==========================================================
# Company Branding
# ==========================================================

class Branding(BaseModel):
    logo_url: Optional[str] = None
    accent_color: str = "#4f46e5"


# ==========================================================
# Companies Collection
# ==========================================================

class Company(MongoBaseModel):
    name: str
    contact_email: str

    allowed_languages: List[str]
    allowed_voices: List[str]
    allowed_strategies: List[str]
    allowed_interview_modes: List[str]
    allowed_llm_tiers: List[str]

    max_campaigns: int

    status: Literal["active", "suspended"]

    branding: Branding

    created_at: datetime = Field(
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

# ==========================================================
# Interview Campaign
# ==========================================================

class VoiceConfig(BaseModel):
    voice_id: str
    language: str
    accent: str


class InterviewCampaign(MongoBaseModel):
    company_id: PyObjectId

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