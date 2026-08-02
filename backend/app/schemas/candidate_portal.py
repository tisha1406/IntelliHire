from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime


# ==============================================================
# Invitation Schemas
# ==============================================================

class InviteCandidateRequest(BaseModel):
    name: str
    email: EmailStr
    campaign_id: str
    target_role: str
    experience_level: str = "mid"


class InviteCandidateResponse(BaseModel):
    candidate_id: str
    user_id: str
    invitation_token: str
    message: str


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
    candidate_name: str
    candidate_email: str

    # Campaign info
    company_name: str
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

class QuestionFeedback(BaseModel):
    id: str
    topic: str
    question: str
    score: int
    feedback: str


class ReportResponse(BaseModel):
    has_report: bool
    overall_score: Optional[int] = None
    technical_score: Optional[int] = None
    communication_score: Optional[int] = None
    confidence: Optional[int] = None
    problem_solving: Optional[int] = None
    soft_skills_score: Optional[int] = None
    time_management: Optional[int] = None
    resume_match: Optional[int] = None
    radar_data: List[dict] = []
    strengths: List[str] = []
    weaknesses: List[str] = []
    improvement_suggestions: List[str] = []
    company_remarks: Optional[str] = None
    question_feedback: List[QuestionFeedback] = []


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
