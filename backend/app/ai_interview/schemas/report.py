from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from app.ai_interview.core.enums import MatchLabel


class TopicResult(BaseModel):
    topic_id: str
    topic_name: str
    score: float
    feedback: str


class ExplainabilitySummary(BaseModel):
    decision_traces: List[Dict[str, Any]] = Field(default_factory=list)


class InterviewReportSchema(BaseModel):
    session_id: str
    overall_score: float
    match_label: MatchLabel

    strengths: List[str] = Field(default_factory=list)
    improvement_areas: List[str] = Field(default_factory=list)

    topic_results: List[TopicResult] = Field(default_factory=list)

    interview_summary: str
    explainability_summary: ExplainabilitySummary
