"""
Phase 5 — Question Orchestration & Interview Turn Engine

QuestionValidator: Deterministic structural validation of GeneratedQuestion output.

This validator MUST NOT:
  - Evaluate semantic quality of the question
  - Score how relevant the question is
  - Evaluate candidate answers
  - Make runtime decisions about topic or difficulty selection

It MUST enforce:
  - Structural presence of required fields
  - Text length bounds (MIN_QUESTION_LENGTH, MAX_QUESTION_LENGTH)
  - question_type matches the selected_question_type in the request
  - difficulty matches the requested difficulty
  - topic_id matches the requested topic_id
  - Basic safety rejection of obvious prompt-injection artifacts
"""
import re

from app.ai_interview.question_engine.config import QuestionEngineConfig
from app.ai_interview.question_engine.schemas import (
    GeneratedQuestion,
    QuestionGenerationRequest,
)
from app.ai_interview.question_engine.exceptions import QuestionValidationError


# Patterns that indicate the generator leaked internal system instructions
# into the output.  These are conservative structural checks only.
_INJECTION_PATTERNS = [
    re.compile(r"\bsystem\s+instruction\b", re.IGNORECASE),
    re.compile(r"\bprompt\s+injection\b", re.IGNORECASE),
    re.compile(r"\bignore\s+previous\s+instructions?\b", re.IGNORECASE),
    re.compile(r"\[INST\]", re.IGNORECASE),
    re.compile(r"<<SYS>>", re.IGNORECASE),
]


class QuestionValidator:
    """
    Validates a GeneratedQuestion against the constraints expressed in the
    QuestionGenerationRequest.

    Raises QuestionValidationError on any structural failure.
    Returns normally when the question is structurally valid.
    No return value (caller catches the exception or proceeds).
    """

    @staticmethod
    def validate(
        question: GeneratedQuestion,
        request: QuestionGenerationRequest,
    ) -> None:
        """
        Run all structural validations.

        Args:
            question: The raw output from the generator.
            request:  The constrained request that prompted generation.

        Raises:
            QuestionValidationError: if any structural check fails.
        """
        # ── 1. Text presence ─────────────────────────────────────────────────
        if not question.question_text or not question.question_text.strip():
            raise QuestionValidationError(
                "Generated question text is empty or whitespace-only."
            )

        text = question.question_text.strip()

        # ── 2. Minimum length ─────────────────────────────────────────────────
        if len(text) < QuestionEngineConfig.MIN_QUESTION_LENGTH:
            raise QuestionValidationError(
                f"Generated question is too short: {len(text)} chars "
                f"(minimum {QuestionEngineConfig.MIN_QUESTION_LENGTH})."
            )

        # ── 3. Maximum length ─────────────────────────────────────────────────
        if len(text) > QuestionEngineConfig.MAX_QUESTION_LENGTH:
            raise QuestionValidationError(
                f"Generated question is too long: {len(text)} chars "
                f"(maximum {QuestionEngineConfig.MAX_QUESTION_LENGTH})."
            )

        # ── 4. Difficulty must match request ──────────────────────────────────
        if question.difficulty != request.difficulty:
            raise QuestionValidationError(
                f"Difficulty mismatch: expected {request.difficulty.value!r}, "
                f"got {question.difficulty.value!r}."
            )

        # ── 5. question_type must match selected_question_type in request ─────
        if question.question_type != request.selected_question_type:
            raise QuestionValidationError(
                f"Question type mismatch: expected {request.selected_question_type.value!r}, "
                f"got {question.question_type.value!r}."
            )

        # ── 6. question_type must be within the allowed set ───────────────────
        if question.question_type not in request.allowed_question_types:
            raise QuestionValidationError(
                f"Question type {question.question_type.value!r} is not in "
                f"the allowed set: {[qt.value for qt in request.allowed_question_types]}."
            )

        # ── 7. topic_id must match ────────────────────────────────────────────
        if question.topic_id != request.topic_id:
            raise QuestionValidationError(
                f"Topic ID mismatch: expected {request.topic_id!r}, "
                f"got {question.topic_id!r}."
            )

        # ── 8. Safety: prompt injection artifact detection ────────────────────
        for pattern in _INJECTION_PATTERNS:
            if pattern.search(text):
                raise QuestionValidationError(
                    f"Generated question contains a disallowed pattern: {pattern.pattern!r}."
                )
