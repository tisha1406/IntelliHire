import uuid
from typing import List, Optional, Dict
from datetime import datetime
from pydantic import BaseModel, Field

from app.ai_interview.answer_engine.enums import (
    EvaluationSignal, 
    CoverageSignal, 
    AnswerValidity, 
    FollowUpSignal, 
    AnswerStatus
)
from app.ai_interview.core.enums import DifficultyLevel, QuestionType

class AnswerSubmission(BaseModel):
    session_id: str
    question_record_id: str
    answer_text: str
    submitted_at: datetime = Field(default_factory=datetime.utcnow)

class ProcessedAnswer(BaseModel):
    original_text: str
    normalized_text: str
    word_count: int
    character_count: int
    validity: AnswerValidity

class EvaluationRequest(BaseModel):
    session_id: str
    question_record_id: str
    topic_id: str
    topic_name: str
    question_text: str
    question_type: QuestionType
    difficulty: DifficultyLevel
    candidate_answer: str
    interview_mode_criteria: Dict[str, str] = Field(default_factory=dict)
    relevant_candidate_context: List[str] = Field(default_factory=list)

class RawEvaluation(BaseModel):
    relevance_score: float
    correctness_score: float
    depth_score: float
    clarity_score: float
    overall_score: float
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    missing_concepts: List[str] = Field(default_factory=list)
    evidence_summary: str
    follow_up_signal: FollowUpSignal = FollowUpSignal.NONE
    qualitative_coverage_signal: CoverageSignal = CoverageSignal.NOT_COVERED

class EvaluationResult(BaseModel):
    evaluation_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    question_record_id: str
    topic_id: str
    overall_score: float
    normalized_dimension_scores: Dict[str, float] = Field(default_factory=dict)
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    missing_concepts: List[str] = Field(default_factory=list)
    evidence_summary: str
    follow_up_signal: FollowUpSignal
    qualitative_coverage_signal: CoverageSignal
    evaluated_at: datetime = Field(default_factory=datetime.utcnow)

class EvaluationRecord(BaseModel):
    evaluation_id: str
    question_record_id: str
    topic_id: str
    overall_score: float
    qualitative_coverage_signal: CoverageSignal
    follow_up_signal: FollowUpSignal
    timestamp: datetime = Field(default_factory=datetime.utcnow)
