"""
Tests for QuestionEngine (full pipeline integration).

Tests cover:
  A. Happy path — valid question generated, validated, dispatched, counters incremented
  B. Invalid generation — retry succeeds on second attempt
  C. Duplicate generation — retry succeeds on second attempt
  D. Retry exhaustion (all attempts fail) — zero counter mutations
  E. Generator raises QuestionGenerationError — no session mutation
  F. Budget exhaustion — generator never called
  G. Deterministic reproducibility with fake generator
  H. Topic state NOT automatically set to qualitatively_covered after dispatch
  I. Denied turn (not in progress) returns failure result without generation
  J. Idempotency semantics: turn_number based on questions_asked_total
"""
import pytest
from datetime import datetime

from app.ai_interview.core.enums import (
    InterviewState, DifficultyLevel, QuestionType, TopicState,
)
from app.ai_interview.runtime.enums import RuntimeAction
from app.ai_interview.runtime.schemas import RuntimeDecision
from app.ai_interview.question_engine.question_engine import QuestionEngine
from app.ai_interview.question_engine.question_generator import FakeQuestionGenerator
from app.ai_interview.question_engine.enums import QuestionEngineFailureCode
from app.ai_interview.question_engine.schemas import GeneratedQuestion
from app.ai_interview.question_engine.exceptions import QuestionGenerationError


# ── A. Happy path ─────────────────────────────────────────────────────────────

def test_happy_path_dispatches_question(
    session_in_progress, runtime_decision_python, candidate_context, interview_mode
):
    engine = QuestionEngine(generator=FakeQuestionGenerator(mode="valid"))
    result = engine.request_next_question(
        session=session_in_progress,
        runtime_decision=runtime_decision_python,
        candidate_context=candidate_context,
        mode=interview_mode,
    )

    assert result.success is True
    assert result.question_record is not None
    assert result.question_sequence_number == 1
    assert result.attempts == 1
    assert result.failure_code is None
    # Counters must have been incremented
    assert session_in_progress.questions_asked_total == 1
    assert session_in_progress.topic_progress[0].questions_asked == 1
    assert len(session_in_progress.question_history) == 1


# ── H. Topic not qualitatively_covered after dispatch ──────────────────────────

def test_qualitative_coverage_not_inferred_from_dispatch(
    session_in_progress, runtime_decision_python, candidate_context, interview_mode
):
    """
    CRITICAL: dispatching all budget questions MUST NOT set qualitatively_covered=True.
    """
    engine = QuestionEngine(generator=FakeQuestionGenerator(mode="valid"))

    # Dispatch all 3 budget questions for the Python topic
    for _ in range(3):
        plan_check = QuestionEngine(generator=FakeQuestionGenerator(mode="valid"))
        result = plan_check.request_next_question(
            session=session_in_progress,
            runtime_decision=runtime_decision_python,
            candidate_context=candidate_context,
            mode=interview_mode,
        )
        if not result.success:
            break  # Budget exhausted legitimately

    # After all questions asked, qualitative coverage must still be False
    python_progress = session_in_progress.topic_progress[0]
    assert python_progress.qualitatively_covered is False
    # TopicState must NOT have changed to COVERED
    assert python_progress.state != TopicState.COVERED


# ── B. Invalid generation retry succeeds ──────────────────────────────────────

class _InvalidThenValidGenerator:
    """Fails on attempt 1, succeeds on attempt 2."""
    def __init__(self):
        self._call_count = 0

    def generate(self, request, attempt_number=1):
        self._call_count += 1
        if self._call_count == 1:
            return GeneratedQuestion(
                question_text="",  # empty — will fail validation
                question_type=request.selected_question_type,
                topic_id=request.topic_id,
                difficulty=request.difficulty,
            )
        return GeneratedQuestion(
            question_text="[Retry] How does Python handle exceptions?",
            question_type=request.selected_question_type,
            topic_id=request.topic_id,
            difficulty=request.difficulty,
        )


def test_retry_on_invalid_generation(
    session_in_progress, runtime_decision_python, candidate_context, interview_mode
):
    engine = QuestionEngine(generator=_InvalidThenValidGenerator())
    result = engine.request_next_question(
        session=session_in_progress,
        runtime_decision=runtime_decision_python,
        candidate_context=candidate_context,
        mode=interview_mode,
    )

    assert result.success is True
    assert result.attempts == 2  # first attempt failed, second succeeded
    assert session_in_progress.questions_asked_total == 1  # only one actual dispatch


# ── C. Duplicate generation retry succeeds ────────────────────────────────────

def test_retry_on_duplicate_generation(
    session_in_progress, runtime_decision_python, candidate_context, interview_mode
):
    """First attempt produces a duplicate; second attempt produces a unique question."""
    # Pre-populate question history with a question that the fake "duplicate" generator will return
    from tests.ai_interview.question_engine.conftest import make_question_record
    first_q = "[Fake Q1] Describe a key concept in Python at medium difficulty (initial question)."
    existing_record = make_question_record(question_text=first_q, turn_number=1)
    session_in_progress.question_history.append(existing_record)
    session_in_progress.questions_asked_total = 1
    session_in_progress.topic_progress[0].questions_asked = 1

    class _DuplicateThenValidGenerator:
        def __init__(self):
            self._call_count = 0

        def generate(self, request, attempt_number=1):
            self._call_count += 1
            if self._call_count == 1:
                return GeneratedQuestion(
                    question_text=first_q,  # exact duplicate
                    question_type=request.selected_question_type,
                    topic_id=request.topic_id,
                    difficulty=request.difficulty,
                )
            return GeneratedQuestion(
                question_text="How does Python's list differ from a tuple? Explain with examples.",
                question_type=request.selected_question_type,
                topic_id=request.topic_id,
                difficulty=request.difficulty,
            )

    engine = QuestionEngine(generator=_DuplicateThenValidGenerator())
    result = engine.request_next_question(
        session=session_in_progress,
        runtime_decision=runtime_decision_python,
        candidate_context=candidate_context,
        mode=interview_mode,
    )

    assert result.success is True
    assert result.attempts == 2
    assert session_in_progress.questions_asked_total == 2  # 1 existing + 1 new


# ── D. Retry exhaustion — zero counter mutations ──────────────────────────────

def test_all_retries_exhausted_no_mutation(
    session_in_progress, runtime_decision_python, candidate_context, interview_mode
):
    engine = QuestionEngine(generator=FakeQuestionGenerator(mode="invalid"))
    before_total = session_in_progress.questions_asked_total
    before_topic = session_in_progress.topic_progress[0].questions_asked
    before_history = len(session_in_progress.question_history)

    result = engine.request_next_question(
        session=session_in_progress,
        runtime_decision=runtime_decision_python,
        candidate_context=candidate_context,
        mode=interview_mode,
    )

    assert result.success is False
    assert result.failure_code == QuestionEngineFailureCode.VALIDATION_FAILED
    assert session_in_progress.questions_asked_total == before_total
    assert session_in_progress.topic_progress[0].questions_asked == before_topic
    assert len(session_in_progress.question_history) == before_history


# ── E. Generator raises — no session mutation ─────────────────────────────────

def test_generator_failure_no_mutation(
    session_in_progress, runtime_decision_python, candidate_context, interview_mode
):
    engine = QuestionEngine(generator=FakeQuestionGenerator(mode="raise"))
    before_total = session_in_progress.questions_asked_total
    before_topic = session_in_progress.topic_progress[0].questions_asked
    before_history = len(session_in_progress.question_history)

    result = engine.request_next_question(
        session=session_in_progress,
        runtime_decision=runtime_decision_python,
        candidate_context=candidate_context,
        mode=interview_mode,
    )

    assert result.success is False
    assert result.failure_code == QuestionEngineFailureCode.GENERATION_FAILED
    # Session must be completely unchanged
    assert session_in_progress.questions_asked_total == before_total
    assert session_in_progress.topic_progress[0].questions_asked == before_topic
    assert len(session_in_progress.question_history) == before_history
    assert session_in_progress.state == InterviewState.IN_PROGRESS


# ── F. Budget exhausted — generator never called ──────────────────────────────

def test_global_budget_exhausted_generator_not_called(
    session_in_progress, runtime_decision_python, candidate_context, interview_mode
):
    class _SpyGenerator:
        def __init__(self):
            self.called = False
        def generate(self, request, attempt_number=1):
            self.called = True
            return GeneratedQuestion(
                question_text="This should never be generated.",
                question_type=request.selected_question_type,
                topic_id=request.topic_id,
                difficulty=request.difficulty,
            )

    spy = _SpyGenerator()
    session_in_progress.questions_asked_total = 5  # == total budget

    engine = QuestionEngine(generator=spy)
    result = engine.request_next_question(
        session=session_in_progress,
        runtime_decision=runtime_decision_python,
        candidate_context=candidate_context,
        mode=interview_mode,
    )

    assert result.success is False
    assert result.failure_code == QuestionEngineFailureCode.TURN_NOT_ALLOWED
    assert spy.called is False  # generator must NOT have been called


# ── G. Deterministic reproducibility ─────────────────────────────────────────

def test_deterministic_reproducibility(
    session_in_progress, runtime_decision_python, candidate_context, interview_mode, blueprint
):
    """
    Same session state + same fake generator → same question text.
    """
    from datetime import datetime
    from app.ai_interview.schemas.session import InterviewSessionSchema, TopicProgress

    def _fresh_session():
        return InterviewSessionSchema(
            session_id="determinism-test",
            candidate_id="cand-001",
            company_id="company-001",
            campaign_id="campaign-001",
            mode_id="mode-001",
            mode_version=1,
            state=InterviewState.IN_PROGRESS,
            blueprint=blueprint,
            questions_asked_total=0,
            current_topic_id="python",
            topic_progress=[
                TopicProgress(topic_id="python", state=TopicState.IN_PROGRESS, questions_asked=0),
                TopicProgress(topic_id="sql", state=TopicState.NOT_STARTED, questions_asked=0),
            ],
            created_at=datetime(2025, 1, 1, 10, 0, 0),
            started_at=datetime(2025, 1, 1, 10, 0, 1),
        )

    engine = QuestionEngine(generator=FakeQuestionGenerator(mode="valid"))

    session_a = _fresh_session()
    session_b = _fresh_session()

    result_a = engine.request_next_question(session_a, runtime_decision_python, candidate_context, interview_mode)
    result_b = engine.request_next_question(session_b, runtime_decision_python, candidate_context, interview_mode)

    assert result_a.success is True
    assert result_b.success is True
    assert result_a.question_record.question_text == result_b.question_record.question_text
    assert result_a.question_record.turn_number == result_b.question_record.turn_number


# ── I. Denied turn — no generation ────────────────────────────────────────────

def test_paused_session_returns_failure_no_generation(
    session_in_progress, runtime_decision_python, candidate_context, interview_mode
):
    session_in_progress.state = InterviewState.PAUSED

    class _SpyGenerator:
        def __init__(self):
            self.called = False
        def generate(self, request, attempt_number=1):
            self.called = True

    spy = _SpyGenerator()
    engine = QuestionEngine(generator=spy)
    result = engine.request_next_question(
        session=session_in_progress,
        runtime_decision=runtime_decision_python,
        candidate_context=candidate_context,
        mode=interview_mode,
    )

    assert result.success is False
    assert result.failure_code == QuestionEngineFailureCode.TURN_NOT_ALLOWED
    assert spy.called is False


# ── J. Turn number idempotency semantics ──────────────────────────────────────

def test_turn_number_equals_questions_asked_plus_one(
    session_in_progress, runtime_decision_python, candidate_context, interview_mode
):
    engine = QuestionEngine(generator=FakeQuestionGenerator(mode="valid"))

    result = engine.request_next_question(
        session=session_in_progress,
        runtime_decision=runtime_decision_python,
        candidate_context=candidate_context,
        mode=interview_mode,
    )

    assert result.success is True
    # turn_number was 1 when dispatched (questions_asked_total was 0)
    assert result.question_record.turn_number == 1

    # After dispatch, questions_asked_total is 1
    # Next turn_number will be 2
    result2 = engine.request_next_question(
        session=session_in_progress,
        runtime_decision=runtime_decision_python,
        candidate_context=candidate_context,
        mode=interview_mode,
    )
    assert result2.success is True
    assert result2.question_record.turn_number == 2
