"""
Phase 5 — Question Orchestration & Interview Turn Engine

QuestionGenerator abstraction + FakeQuestionGenerator.

Architecture:
  QuestionGenerator (Protocol)
      │
      ├── FakeQuestionGenerator  (deterministic, for testing)
      ├── LlamaQuestionGenerator (future)
      └── OpenAIQuestionGenerator (future)

The Protocol ensures that any future provider can be swapped in without
changing any of the orchestration logic in QuestionEngine.

FakeQuestionGenerator rules:
  - Must be FULLY deterministic: same request → same GeneratedQuestion.
  - Uses topic_name + difficulty + selected_question_type + attempt_number
    to derive a stable question text.
  - Supports a configurable `mode` for test scenarios:
      "valid"     — always returns a structurally valid question
      "invalid"   — always returns a question that will fail validation (empty text)
      "duplicate" — always returns the first element of previous_questions
      "raise"     — always raises QuestionGenerationError
"""
from typing import Protocol, runtime_checkable

from app.ai_interview.question_engine.schemas import (
    QuestionGenerationRequest,
    GeneratedQuestion,
)
from app.ai_interview.question_engine.exceptions import QuestionGenerationError


# ---------------------------------------------------------------------------
# Protocol (the interface that all providers must implement)
# ---------------------------------------------------------------------------

@runtime_checkable
class QuestionGenerator(Protocol):
    """
    Abstract generator interface.

    Implementors must never:
      - Mutate InterviewSessionSchema
      - Select a different topic from the one in the request
      - Return a difficulty other than the requested one
      - Return a question_type not in allowed_question_types

    The deterministic validation layer (QuestionValidator) will reject
    any output that violates these constraints.
    """

    def generate(
        self,
        request: QuestionGenerationRequest,
        attempt_number: int = 1,
    ) -> GeneratedQuestion:
        """
        Generate exactly one interview question.

        Args:
            request:        The constrained generation request.
            attempt_number: 1-indexed retry counter (1 = first attempt).

        Returns:
            GeneratedQuestion — structured output, NOT a raw string.

        Raises:
            QuestionGenerationError: if the provider cannot produce output.
        """
        ...


# ---------------------------------------------------------------------------
# FakeQuestionGenerator  (deterministic test double)
# ---------------------------------------------------------------------------

class FakeQuestionGenerator:
    """
    Deterministic mock generator for Phase 5 tests and future CI pipelines.

    This generator requires no external API, network, GPU, or API key.

    Modes
    -----
    "valid"     Always returns a structurally correct GeneratedQuestion.
    "invalid"   Returns a GeneratedQuestion with empty question_text
                (will be rejected by QuestionValidator).
    "duplicate" Returns a GeneratedQuestion whose text matches the first
                entry in request.previous_questions (triggers DuplicateDetector).
                Falls back to "valid" mode if no previous questions exist.
    "raise"     Raises QuestionGenerationError (simulates provider failure).
    """

    def __init__(self, mode: str = "valid") -> None:
        if mode not in {"valid", "invalid", "duplicate", "raise"}:
            raise ValueError(
                f"FakeQuestionGenerator mode must be one of "
                f"'valid', 'invalid', 'duplicate', 'raise'. Got: {mode!r}"
            )
        self._mode = mode

    def generate(
        self,
        request: QuestionGenerationRequest,
        attempt_number: int = 1,
    ) -> GeneratedQuestion:
        """
        Deterministically produce a GeneratedQuestion based on the request.

        Determinism guarantee:
          same topic_name + difficulty + selected_question_type + attempt_number
          → same question_text

        No randomness.  No network calls.  No side effects.
        """
        if self._mode == "raise":
            raise QuestionGenerationError(
                f"FakeQuestionGenerator[raise]: simulated provider failure "
                f"on attempt {attempt_number}."
            )

        if self._mode == "invalid":
            # Return empty text — QuestionValidator will reject this.
            return GeneratedQuestion(
                question_text="",
                question_type=request.selected_question_type,
                topic_id=request.topic_id,
                difficulty=request.difficulty,
                rationale="[fake-invalid]",
            )

        if self._mode == "duplicate":
            if request.previous_questions:
                # Return the first previous question verbatim — DuplicateDetector will catch it.
                dup_text = request.previous_questions[0]
                return GeneratedQuestion(
                    question_text=dup_text,
                    question_type=request.selected_question_type,
                    topic_id=request.topic_id,
                    difficulty=request.difficulty,
                    rationale="[fake-duplicate]",
                )
            # No previous questions — fall through to "valid"

        # "valid" mode (default) — deterministic question text
        question_text = (
            f"[Fake Q{attempt_number}] "
            f"Describe a key concept in {request.topic_name} "
            f"at {request.difficulty.value} difficulty "
            f"({request.selected_question_type.value} question)."
        )
        return GeneratedQuestion(
            question_text=question_text,
            question_type=request.selected_question_type,
            topic_id=request.topic_id,
            difficulty=request.difficulty,
            rationale="[fake-valid]",
        )
