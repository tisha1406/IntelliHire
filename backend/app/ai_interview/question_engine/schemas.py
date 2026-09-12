"""
Phase 5 — Question Orchestration & Interview Turn Engine

All schemas introduced by Phase 5.

Design decisions:
- QuestionRecord is a standalone schema (not reusing InterviewTurnSchema) because
  InterviewTurnSchema contains answer, evaluation, readiness, and decision fields
  that belong to future phases. QuestionRecord records only what Phase 5 can know:
  the dispatched question. Future phases may JOIN QuestionRecord with answer data.
- Forward-reference in InterviewSessionSchema for QuestionRecord uses TYPE_CHECKING
  to avoid circular imports. Pydantic's model_rebuild() resolves it at runtime.
"""
import uuid
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

from app.ai_interview.schemas.session import OperationClaim

from app.ai_interview.core.enums import DifficultyLevel, QuestionType
from app.ai_interview.question_engine.enums import TurnDenialReason, QuestionEngineFailureCode, QuestionStatus


# ---------------------------------------------------------------------------
# QuestionRecord
# ---------------------------------------------------------------------------

class QuestionRecord(BaseModel):
    """
    Represents a single officially-dispatched interview question.

    Ownership: QuestionDispatcher creates and appends this to
    InterviewSessionSchema.question_history ONLY after all validation passes.

    Do NOT store rejected, invalid, or duplicate generation attempts here.
    """
    record_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Stable unique identifier for this dispatched question record."
    )
    # Deterministic turn identity: session_id + turn_number together form a
    # stable composite key suitable for future idempotency enforcement.
    session_id: str
    turn_number: int = Field(
        description=(
            "1-indexed sequence number. Derived from questions_asked_total + 1 "
            "BEFORE the counter is incremented. Same input → same turn_number."
        )
    )

    topic_id: str
    question_text: str
    question_type: QuestionType
    difficulty: DifficultyLevel
    status: QuestionStatus = Field(
        default=QuestionStatus.DISPATCHED,
        description="Tracks the lifecycle state of this turn."
    )
    evaluation_claim: Optional[OperationClaim] = Field(
        default=None, 
        description="Explicit lease for evaluating this answer. Provides crash recovery and fencing."
    )


# ---------------------------------------------------------------------------
# QuestionTurnPlan
# ---------------------------------------------------------------------------

class QuestionTurnPlan(BaseModel):
    """
    Deterministic permission and context object produced by QuestionTurnPlanner.

    When allowed=False the engine must NOT call the generator.
    When allowed=True this plan drives QuestionRequestBuilder.
    """
    session_id: str

    topic_id: str
    topic_name: str

    difficulty: DifficultyLevel
    allowed_question_types: List[QuestionType]

    topic_question_budget: int
    topic_questions_asked: int

    total_question_budget: int
    total_questions_asked: int

    # turn_number = total_questions_asked + 1 (computed when plan is created)
    turn_number: int

    allowed: bool
    denial_reason: Optional[TurnDenialReason] = None


# ---------------------------------------------------------------------------
# QuestionGenerationRequest
# ---------------------------------------------------------------------------

class QuestionGenerationRequest(BaseModel):
    """
    Minimal controlled input sent to the QuestionGenerator.

    The generator receives ONLY what it needs to produce one question.
    It must never receive the full mutable session, the full resume, or
    anything that would allow it to make runtime decisions.
    """
    session_id: str
    turn_number: int

    topic_id: str
    topic_name: str

    difficulty: DifficultyLevel
    allowed_question_types: List[QuestionType]
    # Deterministic: the planner selects one allowed type; the generator must
    # use this type or the validator will reject the output.
    selected_question_type: QuestionType

    # Topic-relevant candidate evidence only (not full resume)
    relevant_skills: List[str] = Field(default_factory=list)
    relevant_projects: List[str] = Field(default_factory=list)
    relevant_experience: List[str] = Field(default_factory=list)

    # Topic-relevant job requirements
    relevant_job_requirements: List[str] = Field(default_factory=list)

    # Bounded previous-question context for duplicate avoidance at generation time.
    # Max length enforced by QuestionRequestBuilder (MAX_PREVIOUS_QUESTIONS_CONTEXT).
    previous_questions: List[str] = Field(default_factory=list)

    # Structural counters for prompt context (informational only — generator
    # must not use these to make runtime decisions).
    question_number: int
    max_questions_for_topic: int


# ---------------------------------------------------------------------------
# GeneratedQuestion
# ---------------------------------------------------------------------------

class GeneratedQuestion(BaseModel):
    """
    Raw structured output from the generator.

    The generator produces this; the validator evaluates it against the request.
    This is NOT an official record — only QuestionRecord (after dispatch) is official.
    """
    question_text: str
    question_type: QuestionType
    topic_id: str
    difficulty: DifficultyLevel
    # Optional: provider rationale for human audit / future observability.
    # Must NOT be used in deterministic logic.
    rationale: Optional[str] = None


# ---------------------------------------------------------------------------
# QuestionEngineResult
# ---------------------------------------------------------------------------

class QuestionEngineResult(BaseModel):
    """
    Public result returned by QuestionEngine.request_next_question().

    Callers should inspect `success` and `failure_code` rather than catching
    internal exceptions. Internal exceptions are translated to this structure.
    """
    success: bool

    # Populated only when success=True
    question_record: Optional[QuestionRecord] = None

    # Optional runtime evaluations
    evaluation: Optional[Dict[str, Any]] = None

    model_config = {"arbitrary_types_allowed": True}

    session_id: str
    topic_id: Optional[str] = None

    # 1-indexed sequence number of the dispatched question (when success=True)
    question_sequence_number: Optional[int] = None

    # Number of generation attempts made (1 on first-attempt success; up to MAX_GENERATION_ATTEMPTS on retries)
    attempts: int = 0

    # Populated only when success=False
    failure_code: Optional[QuestionEngineFailureCode] = None
    failure_detail: Optional[str] = None
