"""
Phase 5 — Question Orchestration & Interview Turn Engine

Typed exceptions.  All failures must leave InterviewSession in a consistent state.
These exceptions are caught internally by QuestionEngine and translated into a
QuestionEngineResult rather than propagating as raw exceptions to callers.
"""


class QuestionEngineError(Exception):
    """Base class for all Phase 5 errors."""


class QuestionTurnDeniedError(QuestionEngineError):
    """
    Raised when the deterministic planner determines that a question may NOT be
    asked in the current session state.  No LLM call is made; no counters change.
    """


class QuestionGenerationError(QuestionEngineError):
    """
    Raised when the generator (real or mock) fails to produce any output.
    Example: LLM timeout, network error, or provider exception.
    No counters must be incremented when this is raised.
    """


class QuestionValidationError(QuestionEngineError):
    """
    Raised when a generated question fails structural validation.
    Examples: empty text, wrong difficulty, wrong question type, text too long.
    No counters must be incremented when this is raised.
    """


class DuplicateQuestionError(QuestionEngineError):
    """
    Raised when the duplicate detector determines the generated question
    is too similar to a previously dispatched question.
    No counters must be incremented when this is raised.
    """


class QuestionBudgetExhaustedError(QuestionEngineError):
    """
    Raised when the planner detects that the global or per-topic question
    budget is exhausted.  The generator must NOT be called in this case.
    No counters must be incremented when this is raised.
    """


class QuestionDispatchError(QuestionEngineError):
    """
    Raised when the dispatcher fails to commit the question to session state
    after a successful generation + validation + duplicate-check cycle.
    The dispatcher must roll back any partial mutations before raising this.
    """
