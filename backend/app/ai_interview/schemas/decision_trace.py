from typing import List, Optional
from pydantic import BaseModel, Field
from app.ai_interview.core.enums import InterviewDecision, DifficultyLevel, DecisionReasonCode


class FollowUpDecisionTrace(BaseModel):
    readiness_score: float
    topic_coverage: float
    follow_up_count: int
    max_follow_ups: int
    remaining_budget: int
    decision: InterviewDecision
    reason_codes: List[DecisionReasonCode] = Field(default_factory=list)


class DifficultyDecisionTrace(BaseModel):
    previous_difficulty: DifficultyLevel
    readiness_score: float
    response_time_score: float
    policy: str
    new_difficulty: DifficultyLevel
    reason_codes: List[DecisionReasonCode] = Field(default_factory=list)


class CompletionDecisionTrace(BaseModel):
    questions_asked_total: int
    min_questions: int
    max_questions: int
    emergency_max_questions: int
    mandatory_topics_attempted: bool
    overall_confidence: float
    threshold: float
    decision: InterviewDecision
    reason_codes: List[DecisionReasonCode] = Field(default_factory=list)
