"""
Phase 5 — Question Orchestration & Interview Turn Engine

QuestionEngine: The Phase 5 orchestration facade.

Complete pipeline:
  1. QuestionTurnPlanner   — deterministic permission + budget check
  2. QuestionRequestBuilder — minimal bounded generation request
  3. QuestionGenerator     — pluggable provider (fake for Phase 5)
  4. QuestionValidator     — structural validation
  5. DuplicateDetector     — normalised exact-match duplicate prevention
  6. Retry loop            — up to MAX_GENERATION_ATTEMPTS
  7. QuestionDispatcher    — atomic session mutation
  8. Return QuestionEngineResult

LLM boundary guarantee:
  The generator sees ONLY QuestionGenerationRequest.
  It cannot observe or influence:
    - InterviewState
    - TopicState
    - topic selection
    - budget
    - difficulty policy
    - completion logic
    - counters

Counter guarantee:
  session.questions_asked_total and topic_progress.questions_asked increment
  ONLY inside QuestionDispatcher.dispatch(), which is called ONLY after all
  validation and duplicate checks have passed.

Failure safety:
  Any exception from steps 3–5 is caught, the retry counter advances,
  and — critically — NO session state is mutated.
  After MAX_GENERATION_ATTEMPTS, a QuestionEngineResult with success=False
  is returned. The session remains in its exact pre-call state.
"""
from app.ai_interview.question_engine.config import QuestionEngineConfig
from app.ai_interview.question_engine.enums import QuestionEngineFailureCode
from app.ai_interview.question_engine.schemas import (
    QuestionEngineResult,
    QuestionTurnPlan,
)
from app.ai_interview.question_engine.exceptions import (
    QuestionTurnDeniedError,
    QuestionGenerationError,
    QuestionValidationError,
    DuplicateQuestionError,
    QuestionDispatchError,
)
from app.ai_interview.question_engine.question_turn_planner import QuestionTurnPlanner
from app.ai_interview.question_engine.question_request_builder import QuestionRequestBuilder
from app.ai_interview.question_engine.question_generator import QuestionGenerator
from app.ai_interview.question_engine.question_validator import QuestionValidator
from app.ai_interview.question_engine.duplicate_detector import DuplicateDetector
from app.ai_interview.question_engine.question_dispatcher import QuestionDispatcher

from app.ai_interview.runtime.schemas import RuntimeDecision
from app.ai_interview.schemas.session import InterviewSessionSchema
from app.ai_interview.resume_processing.schemas import CandidateInterviewContext
from app.ai_interview.schemas.interview_mode import InterviewModeDefinition


class QuestionEngine:
    """
    Phase 5 orchestration facade.

    Usage:
        engine = QuestionEngine(generator=FakeQuestionGenerator())
        result = engine.request_next_question(
            session=session,
            runtime_decision=decision,
            candidate_context=context,
            mode=mode,
        )
    """

    def __init__(self, generator: QuestionGenerator) -> None:
        """
        Args:
            generator: Any object implementing the QuestionGenerator Protocol.
                       In Phase 5 this will always be FakeQuestionGenerator.
                       In future phases this can be LlamaQuestionGenerator, etc.
        """
        self._generator = generator

    def request_next_question(
        self,
        session: InterviewSessionSchema,
        runtime_decision: RuntimeDecision,
        candidate_context: CandidateInterviewContext,
        mode: InterviewModeDefinition,
    ) -> QuestionEngineResult:
        """
        Attempt to generate, validate, and dispatch the next question.

        Args:
            session:           Mutable session — will be mutated ONLY on success.
            runtime_decision:  Output of RuntimeController.get_allowed_action().
                               QuestionEngine never calls RuntimeController itself.
            candidate_context: Structured resume context from Phase 2.
            mode:              InterviewModeDefinition from Phase 1.

        Returns:
            QuestionEngineResult with success=True and the QuestionRecord on
            successful dispatch, or success=False with a failure_code on any failure.
        """
        # ── Step 1: Deterministic turn planning ───────────────────────────────
        plan: QuestionTurnPlan = QuestionTurnPlanner.plan(session, runtime_decision)

        if not plan.allowed:
            return QuestionEngineResult(
                success=False,
                session_id=session.session_id,
                topic_id=plan.topic_id or None,
                attempts=0,
                failure_code=QuestionEngineFailureCode.TURN_NOT_ALLOWED,
                failure_detail=f"Turn denied: {plan.denial_reason.value if plan.denial_reason else 'unknown'}",
            )

        # ── Step 2: Build request ─────────────────────────────────────────────
        gen_request = QuestionRequestBuilder.build(
            plan=plan,
            candidate_context=candidate_context,
            mode=mode,
            question_history=session.question_history,
        )

        # ── Steps 3–5: Generate → Validate → Duplicate check (with retries) ──
        max_attempts = QuestionEngineConfig.MAX_GENERATION_ATTEMPTS
        last_failure_code: QuestionEngineFailureCode = QuestionEngineFailureCode.ALL_ATTEMPTS_FAILED
        last_failure_detail: str = "No attempts made."

        for attempt in range(1, max_attempts + 1):
            try:
                # Step 3: Generate (LLM boundary)
                generated = self._generator.generate(
                    request=gen_request,
                    attempt_number=attempt,
                )
            except QuestionGenerationError as exc:
                last_failure_code = QuestionEngineFailureCode.GENERATION_FAILED
                last_failure_detail = str(exc)
                continue  # retry

            try:
                # Step 4: Structural validation
                QuestionValidator.validate(generated, gen_request)
            except QuestionValidationError as exc:
                last_failure_code = QuestionEngineFailureCode.VALIDATION_FAILED
                last_failure_detail = str(exc)
                continue  # retry

            try:
                # Step 5: Duplicate detection
                DuplicateDetector.check(
                    candidate_text=generated.question_text,
                    question_history=session.question_history,
                )
            except DuplicateQuestionError as exc:
                last_failure_code = QuestionEngineFailureCode.DUPLICATE_EXHAUSTED
                last_failure_detail = str(exc)
                continue  # retry

            # All checks passed — dispatch (this is the only mutation point)
            try:
                record = QuestionDispatcher.dispatch(
                    session=session,
                    plan=plan,
                    question=generated,
                )
            except QuestionDispatchError as exc:
                return QuestionEngineResult(
                    success=False,
                    session_id=session.session_id,
                    topic_id=plan.topic_id,
                    attempts=attempt,
                    failure_code=QuestionEngineFailureCode.DISPATCH_FAILED,
                    failure_detail=str(exc),
                )

            # ── Success ────────────────────────────────────────────────────────
            return QuestionEngineResult(
                success=True,
                question_record=record,
                session_id=session.session_id,
                topic_id=plan.topic_id,
                question_sequence_number=record.turn_number,
                attempts=attempt,
            )

        # ── All attempts exhausted ────────────────────────────────────────────
        # CRITICAL: No counter was incremented. Session remains consistent.
        return QuestionEngineResult(
            success=False,
            session_id=session.session_id,
            topic_id=plan.topic_id,
            attempts=max_attempts,
            failure_code=last_failure_code,
            failure_detail=(
                f"All {max_attempts} generation attempts failed. "
                f"Last failure: {last_failure_detail}"
            ),
        )
