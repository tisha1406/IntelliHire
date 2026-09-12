"""
Phase 9 — Typed WebSocket Event Schemas (Server → Client)
===========================================================
Every message from the server must conform to one of these schemas.

Design rules:
- The base ServerEvent carries fields every client can rely on.
- ``sequence`` is a monotonic per-connection counter.  It lets clients detect
  dropped messages without requiring persistent event history.
- ``correlation_id`` echoes the ``command_id`` that triggered the event,
  enabling the client to match events to commands.
- No LLM prompts, raw evaluation internals, API keys, or claim metadata
  may appear in any data submodel.
- ``answer_text`` is NEVER included in any event — only ``answer_length``.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import List, Literal, Optional

from pydantic import BaseModel, Field


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Base envelope
# ---------------------------------------------------------------------------

class ServerEvent(BaseModel):
    """Common envelope present on every server → client message."""
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_type: str
    session_id: str
    timestamp: str = Field(default_factory=_utc_now)
    sequence: int = 0           # Set by EventEmitter before sending
    correlation_id: Optional[str] = None   # Mirrors the command_id that caused this


# ---------------------------------------------------------------------------
# Data payloads
# ---------------------------------------------------------------------------

class QuestionSnapshotData(BaseModel):
    """Minimal candidate-visible question snapshot (never include evaluation internals)."""
    record_id: str
    question_text: str
    topic_id: str
    topic_name: Optional[str] = None
    turn_number: int
    question_type: str
    difficulty: str
    status: str


class EvaluationCompleteData(BaseModel):
    """
    Candidate-safe evaluation summary.

    Fields withheld: raw LLM evidence_summary, per-dimension scores,
    internal follow_up decision, missing_concepts list.
    """
    question_record_id: str
    topic_id: str
    overall_score: float              # 0.0–1.0
    follow_up_signal: str             # FollowUpSignal enum value
    qualitative_coverage_signal: str  # CoverageSignal enum value


class SessionSnapshotData(BaseModel):
    """
    Full candidate-safe view of the current interview state.

    Exposed after every reconnect and on-demand from GET /sessions/{id}.
    Internal fields withheld: version, claims, blueprint internals,
    evaluation internals, LLM provider details.
    """
    session_id: str
    interview_state: str            # InterviewState value
    questions_asked_total: int
    total_question_budget: int
    min_questions: int
    current_topic_id: Optional[str] = None
    current_question: Optional[QuestionSnapshotData] = None   # only when DISPATCHED
    is_paused: bool
    is_completed: bool
    is_failed: bool
    waiting_for_answer: bool
    # Recovery hints
    evaluation_in_progress: bool = False
    pending_evaluation: bool = False


class InterviewStartedData(BaseModel):
    mode_id: str
    mode_version: int
    topics_count: int
    total_question_budget: int
    min_questions: int


class QuestionGeneratingData(BaseModel):
    topic_id: str
    turn_number: int


class QuestionReadyData(BaseModel):
    record_id: str
    question_text: str
    topic_id: str
    topic_name: Optional[str] = None
    turn_number: int
    question_type: str
    difficulty: str


class AnswerReceivedData(BaseModel):
    question_record_id: str
    answer_length: int   # character count — NOT answer_text


class EvaluationProcessingData(BaseModel):
    question_record_id: str


class DecisionReadyData(BaseModel):
    action: str   # "next_question" | "complete"
    topic_id: Optional[str] = None


class InterviewCompletedData(BaseModel):
    questions_asked_total: int
    completed_at: str


class InterviewFailedData(BaseModel):
    reason: str   # safe message only, no internal detail


class ConnectionReadyData(BaseModel):
    candidate_id: str
    session_state: str


# ---------------------------------------------------------------------------
# Typed event models
# ---------------------------------------------------------------------------

class ConnectionReadyEvent(ServerEvent):
    event_type: Literal["connection_ready"] = "connection_ready"
    data: ConnectionReadyData


class SessionSnapshotEvent(ServerEvent):
    event_type: Literal["session_snapshot"] = "session_snapshot"
    data: SessionSnapshotData


class InterviewStartedEvent(ServerEvent):
    event_type: Literal["interview_started"] = "interview_started"
    data: InterviewStartedData


class QuestionGeneratingEvent(ServerEvent):
    event_type: Literal["question_generating"] = "question_generating"
    data: QuestionGeneratingData


class QuestionReadyEvent(ServerEvent):
    event_type: Literal["question_ready"] = "question_ready"
    data: QuestionReadyData


class AnswerReceivedEvent(ServerEvent):
    event_type: Literal["answer_received"] = "answer_received"
    data: AnswerReceivedData


class EvaluationProcessingEvent(ServerEvent):
    event_type: Literal["evaluation_processing"] = "evaluation_processing"
    data: EvaluationProcessingData


class EvaluationCompleteEvent(ServerEvent):
    event_type: Literal["evaluation_complete"] = "evaluation_complete"
    data: EvaluationCompleteData


class DecisionReadyEvent(ServerEvent):
    event_type: Literal["decision_ready"] = "decision_ready"
    data: DecisionReadyData


class NextQuestionReadyEvent(ServerEvent):
    event_type: Literal["next_question_ready"] = "next_question_ready"
    data: QuestionReadyData


class InterviewPausedEvent(ServerEvent):
    event_type: Literal["interview_paused"] = "interview_paused"
    data: dict = Field(default_factory=dict)


class InterviewResumedEvent(ServerEvent):
    event_type: Literal["interview_resumed"] = "interview_resumed"
    data: dict = Field(default_factory=dict)


class InterviewCompletedEvent(ServerEvent):
    event_type: Literal["interview_completed"] = "interview_completed"
    data: InterviewCompletedData


class InterviewFailedEvent(ServerEvent):
    event_type: Literal["interview_failed"] = "interview_failed"
    data: InterviewFailedData


class ErrorEvent(ServerEvent):
    event_type: Literal["error"] = "error"
    data: "WsErrorPayload"


class PongEvent(ServerEvent):
    event_type: Literal["pong"] = "pong"
    data: dict = Field(default_factory=dict)


class ConnectionReplacedEvent(ServerEvent):
    event_type: Literal["connection_replaced"] = "connection_replaced"
    data: dict = Field(default_factory=dict)


# Resolve forward reference
from app.ai_interview.transport.schemas.ws_errors import WsErrorPayload  # noqa: E402
ErrorEvent.model_rebuild()
