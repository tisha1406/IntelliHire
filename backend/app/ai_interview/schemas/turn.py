from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from app.ai_interview.core.enums import DifficultyLevel, QuestionType, InterviewDecision
from app.ai_interview.schemas.evaluation import AnswerEvaluation
from app.ai_interview.schemas.readiness import ReadinessResult


class TurnTimestamps(BaseModel):
    started_at: datetime
    answered_at: Optional[datetime] = None
    evaluated_at: Optional[datetime] = None


class InterviewTurnSchema(BaseModel):
    session_id: str
    turn_number: int

    topic_id: str
    difficulty: DifficultyLevel
    question_type: QuestionType

    question: str
    answer: Optional[str] = None

    evaluation: Optional[AnswerEvaluation] = None
    readiness: Optional[ReadinessResult] = None

    decision: Optional[InterviewDecision] = None

    timestamps: TurnTimestamps
