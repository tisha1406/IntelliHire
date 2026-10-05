from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Literal
from datetime import datetime


# ==============================================================
# Invitation Schemas
# ==============================================================

class InviteCandidateRequest(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None
    campaign_id: str
    interview_type: Optional[str] = "ai"
    assigned_recruiter_id: Optional[str] = None


class CandidateInfo(BaseModel):
    id: str
    name: str
    email: str
    username: str
    company_id: str
    campaign_id: str
    assigned_recruiter_id: Optional[str] = None
    status: str

class CredentialsInfo(BaseModel):
    username: str
    temporary_password: str

class InviteCandidateResponse(BaseModel):
    candidate: CandidateInfo
    credentials: CredentialsInfo


class AcceptInvitationRequest(BaseModel):
    token: str
    password: str


class AcceptInvitationResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    role: str


# ==============================================================
# Dashboard Schemas
# ==============================================================

class WorkflowStepOut(BaseModel):
    key: str
    label: str
    status: str
    completed_at: Optional[str] = None


class DashboardResponse(BaseModel):
    # Candidate info
    candidate_id: str
    candidate_name: str
    candidate_email: str

    # Campaign info
    company_id: str
    company_name: str
    campaign_id: str
    campaign_name: str
    job_position: str
    deadline: Optional[str] = None
    interview_duration: Optional[str] = None
    interview_type: Optional[str] = None
    interview_language: Optional[str] = None
    interview_strategy: Optional[str] = None

    # Workflow
    stage: str
    next_action: str
    readiness_score: int
    steps: List[WorkflowStepOut]

    # Checkpoint-5 fix: the candidate's own completed official interview
    # session_id, so the dashboard's "View Report" action (next_action ==
    # "VIEW_REPORT") can deep-link straight to
    # /candidate/reports?session_id=... instead of a bare /candidate/reports
    # (which has no session to show). None until official_completed is True.
    official_session_id: Optional[str] = None


# ==============================================================
# Resume Schemas
# ==============================================================

class ResumeStatusResponse(BaseModel):
    has_resume: bool
    status: Optional[str] = None          # "processing" | "analysed" | None
    uploaded_at: Optional[str] = None


class ResumeAnalysisResponse(BaseModel):
    overall_score: int
    ats_score: int
    role_match: int
    completeness: int
    technical_skills: List[str]
    soft_skills: List[str]
    missing_skills: List[str]
    certifications: List[str]
    radar_data: List[dict]
    strengths: List[str]
    weaknesses: List[str]
    improve_ats: str
    missing_keywords: List[str]
    grammar_score: int
    formatting_score: int
    timeline: List[dict]


# ==============================================================
# Documents Schemas
# ==============================================================

class DocumentOut(BaseModel):
    id: str
    name: str
    type: str
    status: str
    date: str


class DocumentsResponse(BaseModel):
    documents: List[DocumentOut]


# ==============================================================
# Report Schemas
# ==============================================================

# ==============================================================
# Report Schemas (D-02)
#
# Reconciled directly against the LIVE output of
# app.services.interview_result_service.InterviewResultService
# .generate_result_report() as of D-01. Every field here corresponds to an
# actual key that service returns — nothing invented, nothing preserved
# merely because an earlier (stale, mock-era) version of this schema had it.
#
# generate_result_report() returns one of three shapes depending on
# session.state and whether any evaluations exist:
#   - IN_PROGRESS / COMPLETED_NO_DATA: only
#     {session_id, status, has_report=False, message}
#   - COMPLETED (has data): the full shape below, with no "message" key.
# This is why every field below session_id/status/has_report is Optional —
# that optionality reflects genuine conditional absence in the service
# output, not defensive guessing.
# ==============================================================

class QuestionFeedbackItem(BaseModel):
    """Matches InterviewResultService._build_question_feedback() exactly."""
    id: str
    question_record_id: str
    topic_id: str
    topic: str
    question: str
    difficulty: Optional[str] = None
    question_type: Optional[str] = None
    # 0.0-1.0 (round(ev.overall_score, 2)) — distinct from score_100.
    score: float
    # 0-100, for direct display.
    score_100: int
    coverage_signal: Optional[str] = None
    follow_up_signal: Optional[str] = None
    evaluated_at: Optional[str] = None


class TopicScore(BaseModel):
    """Matches InterviewResultService._build_topic_scores() exactly.
    questions_asked is the pre-existing INT count — unchanged by D-01, and
    distinct from TopicEvidence.questions_asked (a list) below."""
    topic_id: str
    topic_name: str
    questions_asked: int
    answers_evaluated: int
    average_score: float
    score_100: int
    strong_answers: int
    partial_answers: int
    weak_answers: int
    insufficient_answers: int
    qualitatively_covered: bool
    coverage_score: float


class QuestionRecordDetail(BaseModel):
    """One entry of TopicEvidence.questions_asked — matches the dict built
    in InterviewResultService._build_topic_evidence() exactly."""
    record_id: str
    question_text: str
    question_type: Optional[str] = None
    difficulty: Optional[str] = None
    category: Optional[str] = None
    turn_number: int
    asked_at: Optional[str] = None


# Report-layer vocabulary only (D-01 design decision) — intentionally NOT
# moved into app.ai_interview.core.enums, since it is a report-aggregation
# rollup, not an interview-engine decision input. A constrained Literal is
# the project's existing convention for a fixed string vocabulary that does
# not need its own enum class.
FinalAssessment = Literal["strong", "acceptable", "basic", "insufficient", "not_demonstrated"]


class TopicEvidence(BaseModel):
    """D-01 evidence-model block. Matches
    InterviewResultService._build_topic_evidence() exactly. A sibling list to
    topic_scores — NOT merged into it, so TopicScore.questions_asked (int)
    is never renamed or overloaded by this model's questions_asked (list)."""
    topic_id: str
    topic_name: str
    # The actual dispatched question records for this topic. Empty for a
    # topic that was never reached (see skip_reason below) — never fabricated.
    questions_asked: List[QuestionRecordDetail] = []
    resume_evidence: Optional[Literal["absent", "partial", "strong"]] = None
    # What the candidate said — never proof, never scored.
    candidate_claim: Optional[str] = None
    interview_evidence: Optional[
        Literal["not_demonstrated", "basic", "acceptable", "strong"]
    ] = None
    # Always populated by the service (_derive_final_assessment always
    # returns a value, including "not_demonstrated" for zero evaluations).
    final_assessment: FinalAssessment
    followup_depth: int
    followup_categories_used: List[str] = []
    # Only set when the topic was genuinely never attempted; None otherwise.
    skip_reason: Optional[str] = None


class RequirementCoverageBucket(BaseModel):
    total: int
    verified: int
    not_verified: int
    never_reached: int


class RequirementCoverage(BaseModel):
    """Matches InterviewResultService._build_requirement_coverage_summary()
    exactly. Keys of by_criticality are RequirementCriticality values
    ("critical"|"required"|"preferred"|"resume_only") plus "unspecified"."""
    by_criticality: Dict[str, RequirementCoverageBucket]
    total_topics: int
    total_verified: int
    total_not_verified: int
    total_never_reached: int


class ReportResponse(BaseModel):
    """Reconciled against the live service output — see module note above."""
    session_id: str
    status: Literal["COMPLETED", "IN_PROGRESS", "COMPLETED_NO_DATA"]
    has_report: bool

    # Present only on the two early-return (non-COMPLETED-with-data) shapes.
    message: Optional[str] = None

    # Present only when status == "COMPLETED" and evaluations exist.
    overall_score: Optional[int] = None
    question_count: Optional[int] = None
    completed_at: Optional[str] = None
    question_feedback: Optional[List[QuestionFeedbackItem]] = None
    topic_scores: Optional[List[TopicScore]] = None
    strengths: Optional[List[str]] = None
    weaknesses: Optional[List[str]] = None
    improvement_suggestions: Optional[List[str]] = None
    company_remarks: Optional[str] = None
    # D-01 additions:
    requirement_coverage: Optional[RequirementCoverage] = None
    topic_evidence: Optional[List[TopicEvidence]] = None


# ==============================================================
# Profile Schemas
# ==============================================================

class ProfileResponse(BaseModel):
    candidate_id: str
    name: str
    email: str
    phone: Optional[str] = None
    company_name: str
    campaign_name: str
    job_position: str
    member_since: str
    avatar_url: Optional[str] = None


class ProfileUpdateRequest(BaseModel):
    phone: Optional[str] = None
    avatar_url: Optional[str] = None


# ==============================================================
# Settings Schemas
# ==============================================================

class SettingsResponse(BaseModel):
    high_contrast: bool
    reduced_motion: bool
    sidebar_auto_collapse: bool
    interview_reminders: bool
    company_updates: bool
    result_notifications: bool
    portal_language: str
    live_subtitles: bool


class SettingsUpdateRequest(BaseModel):
    high_contrast: Optional[bool] = None
    reduced_motion: Optional[bool] = None
    sidebar_auto_collapse: Optional[bool] = None
    interview_reminders: Optional[bool] = None
    company_updates: Optional[bool] = None
    result_notifications: Optional[bool] = None
    portal_language: Optional[str] = None
    live_subtitles: Optional[bool] = None


# ==============================================================
# Notifications Schemas
# ==============================================================

class NotificationOut(BaseModel):
    id: str
    type: str
    title: str
    message: str
    read: bool
    created_at: str


class NotificationsResponse(BaseModel):
    notifications: List[NotificationOut]
    unread_count: int


class MarkReadRequest(BaseModel):
    notification_ids: Optional[List[str]] = None   # None = mark all


# ==============================================================
# Support Schemas
# ==============================================================

class FAQOut(BaseModel):
    id: str
    question: str
    answer: str


class TicketOut(BaseModel):
    id: str
    subject: str
    message: str
    status: str
    created_at: str


class SupportResponse(BaseModel):
    faqs: List[FAQOut]
    tickets: List[TicketOut]


class CreateTicketRequest(BaseModel):
    subject: str
    message: str


class CreateTicketResponse(BaseModel):
    ticket_id: str
    status: str


# ==============================================================
# Practice Schemas
# ==============================================================

class PracticeStatusResponse(BaseModel):
    status: str          # "not_started" | "in_progress" | "completed"
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    duration_minutes: Optional[int] = None


class StartPracticeResponse(BaseModel):
    status: str
    started_at: str
    message: str


class CompletePracticeResponse(BaseModel):
    status: str
    completed_at: str
    message: str


# ==============================================================
# Interview Schemas
# ==============================================================

class InterviewStatusResponse(BaseModel):
    status: str          # "locked" | "available" | "in_progress" | "completed"
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    session_id: Optional[str] = None
    message: str


class StartInterviewResponse(BaseModel):
    session_id: str
    status: str
    redirect_url: str


# ==============================================================
# Activity Log Schemas
# ==============================================================

class ActivityEntryOut(BaseModel):
    id: str
    event: str
    description: str
    created_at: str


class ActivityResponse(BaseModel):
    activities: List[ActivityEntryOut]
