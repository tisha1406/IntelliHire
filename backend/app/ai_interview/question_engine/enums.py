"""
Phase 5 — Question Orchestration & Interview Turn Engine

Internal enums specific to the question engine.
Reuses existing core enums wherever possible; this file introduces ONLY
Phase 5-specific reason codes that do not belong in the Phase 1–4 core.
"""
from enum import Enum


class TurnDenialReason(str, Enum):
    """
    Deterministic reason a question turn was denied.
    Returned inside QuestionTurnPlan when allowed=False.
    These are distinct from DecisionReasonCode (which belongs to runtime/completion logic).
    """
    INTERVIEW_NOT_IN_PROGRESS = "interview_not_in_progress"
    RUNTIME_DOES_NOT_AUTHORIZE = "runtime_does_not_authorize"
    NO_ACTIVE_TOPIC = "no_active_topic"
    TOPIC_NOT_FOUND_IN_BLUEPRINT = "topic_not_found_in_blueprint"
    GLOBAL_BUDGET_EXHAUSTED = "global_budget_exhausted"
    TOPIC_BUDGET_EXHAUSTED = "topic_budget_exhausted"


class QuestionEngineFailureCode(str, Enum):
    """
    Structured failure codes returned in QuestionEngineResult when success=False.
    Allows callers to react deterministically without catching multiple exception types.
    """
    TURN_NOT_ALLOWED = "turn_not_allowed"
    GENERATION_FAILED = "generation_failed"
    VALIDATION_FAILED = "validation_failed"
    DUPLICATE_EXHAUSTED = "duplicate_exhausted"
    ALL_ATTEMPTS_FAILED = "all_attempts_failed"
    DISPATCH_FAILED = "dispatch_failed"


class QuestionStatus(str, Enum):
    """
    Tracks the lifecycle of an individual question turn (Phase 7).
    """
    GENERATED = "generated"
    DISPATCHED = "dispatched"
    ANSWER_RECEIVED = "answer_received"
    EVALUATION_PENDING = "evaluation_pending"
    EVALUATING = "evaluating"
    EVALUATED = "evaluated"
