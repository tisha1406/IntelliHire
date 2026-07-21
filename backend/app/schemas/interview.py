from pydantic import BaseModel
from typing import Optional


class InterviewStartRequest(BaseModel):
    language: Optional[str] = None
    domain: Optional[str] = None


class InterviewStartResponse(BaseModel):
    session_id: str


class InterviewQuestionResponse(BaseModel):
    question: str
    audio_reference: str


class InterviewAnswerResponse(BaseModel):
    evaluation_summary: str
    next_question: str | None = None
    completed: bool


class InterviewReportResponse(BaseModel):
    report: dict