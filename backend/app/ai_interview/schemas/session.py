from typing import Any, List, Optional, TYPE_CHECKING
from pydantic import BaseModel, Field, model_validator
from datetime import datetime, timezone
from app.ai_interview.core.enums import InterviewState, TopicState, DifficultyLevel
from app.ai_interview.schemas.blueprint import InterviewBlueprint
if TYPE_CHECKING:
    from app.ai_interview.question_engine.schemas import QuestionRecord
    from app.ai_interview.answer_engine.schemas import EvaluationRecord


class OperationClaim(BaseModel):
    claim_id: str
    claimed_at: datetime
    expires_at: datetime

class TopicEvaluationAggregate(BaseModel):
    answers_evaluated: int = 0
    cumulative_score: float = 0.0
    average_score: float = 0.0
    strong_answers: int = 0
    partial_answers: int = 0
    weak_answers: int = 0
    insufficient_answers: int = 0

class TopicProgress(BaseModel):
    topic_id: str
    state: TopicState = TopicState.NOT_STARTED
    structurally_attempted: bool = False
    qualitatively_covered: bool = False
    coverage_score: float = 0.0
    readiness_score: float = 0.0
    follow_up_count: int = 0
    questions_asked: int = Field(
        default=0,
        description="Count of questions officially dispatched for this topic. Incremented only by QuestionDispatcher after successful dispatch."
    )
    evaluation_aggregate: TopicEvaluationAggregate = Field(default_factory=TopicEvaluationAggregate)

    @model_validator(mode="after")
    def validate_semantics(self) -> "TopicProgress":
        if self.state == TopicState.COVERED:
            if not self.structurally_attempted or not self.qualitatively_covered:
                raise ValueError("COVERED state requires structurally_attempted=True and qualitatively_covered=True")
        elif self.state == TopicState.FAILED_ABANDONED:
            if not self.structurally_attempted or self.qualitatively_covered:
                raise ValueError("FAILED_ABANDONED state requires structurally_attempted=True and qualitatively_covered=False")
        return self


class InterviewSessionSchema(BaseModel):
    session_id: str
    candidate_id: str
    company_id: str
    campaign_id: str

    mode_id: str
    mode_version: int

    state: InterviewState = InterviewState.CREATED

    blueprint: InterviewBlueprint

    questions_asked_total: int = Field(default=0, description="questions_asked_total increments ONLY after a question has: 1. Passed/been accepted by the required validation flow, AND 2. Actually been successfully dispatched to the candidate.")

    generation_claim: Optional[OperationClaim] = Field(default=None, description="Explicit lease for generating questions. Provides crash recovery and fencing.")

    current_topic_id: Optional[str] = None
    current_difficulty: Optional[DifficultyLevel] = None

    topic_progress: List[TopicProgress] = Field(default_factory=list)

    # Official dispatched question history. Appended ONLY by QuestionDispatcher after
    # successful dispatch. Do NOT store failed/rejected/duplicate attempts here.
    # QuestionDispatcher enforces the QuestionRecord type at dispatch time.
    question_history: List["QuestionRecord"] = Field(default_factory=list)

    # Official applied evaluation history. Appended ONLY by EvaluationApplicator after
    # successful validation and coverage assessment.
    evaluation_history: List["EvaluationRecord"] = Field(default_factory=list)

    # Optimistic Concurrency Control (OCC) Revision
    version: int = Field(default=1, description="OCC Revision")
    
    # Persistence Schema Format Revision
    schema_version: int = Field(default=1, description="Persistence Format Revision")

    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    failure_reason: Optional[str] = None

    model_config = {"arbitrary_types_allowed": True}

from app.ai_interview.question_engine.schemas import QuestionRecord
from app.ai_interview.answer_engine.schemas import EvaluationRecord

InterviewSessionSchema.model_rebuild(_types_namespace={
    "QuestionRecord": QuestionRecord,
    "EvaluationRecord": EvaluationRecord
})
