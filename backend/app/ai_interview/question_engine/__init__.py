"""
Phase 5 — Question Orchestration & Interview Turn Engine

Public package interface.
"""
from .question_engine import QuestionEngine
from .question_generator import QuestionGenerator, FakeQuestionGenerator
from .schemas import (
    QuestionTurnPlan,
    QuestionGenerationRequest,
    GeneratedQuestion,
    QuestionRecord,
    QuestionEngineResult,
)
from .enums import TurnDenialReason, QuestionEngineFailureCode
from .exceptions import (
    QuestionEngineError,
    QuestionTurnDeniedError,
    QuestionGenerationError,
    QuestionValidationError,
    DuplicateQuestionError,
    QuestionBudgetExhaustedError,
    QuestionDispatchError,
)

__all__ = [
    # Facade
    "QuestionEngine",
    # Generator abstraction
    "QuestionGenerator",
    "FakeQuestionGenerator",
    # Schemas
    "QuestionTurnPlan",
    "QuestionGenerationRequest",
    "GeneratedQuestion",
    "QuestionRecord",
    "QuestionEngineResult",
    # Enums
    "TurnDenialReason",
    "QuestionEngineFailureCode",
    # Exceptions
    "QuestionEngineError",
    "QuestionTurnDeniedError",
    "QuestionGenerationError",
    "QuestionValidationError",
    "DuplicateQuestionError",
    "QuestionBudgetExhaustedError",
    "QuestionDispatchError",
]
