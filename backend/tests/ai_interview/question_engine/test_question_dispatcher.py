"""
Tests for QuestionDispatcher.

Verifies:
  A. Successful dispatch: question history appended, both counters incremented
  B. Global counter increments by exactly 1
  C. Topic counter increments by exactly 1
  D. InterviewState is NOT mutated
  E. TopicState is NOT mutated
  F. qualitatively_covered is NOT mutated
  G. Counter drift detection prevents dispatch
  H. Global budget check prevents dispatch
  I. Failed dispatch leaves session consistent (rollback)
  J. QuestionRecord contains correct data
"""
import pytest
from datetime import datetime

from app.ai_interview.core.enums import (
    InterviewState, DifficultyLevel, QuestionType, TopicState,
)
from app.ai_interview.question_engine.schemas import GeneratedQuestion
from app.ai_interview.question_engine.question_dispatcher import QuestionDispatcher
from app.ai_interview.question_engine.exceptions import QuestionDispatchError
from app.ai_interview.question_engine.question_turn_planner import QuestionTurnPlanner


def _get_plan(session_in_progress, runtime_decision_python):
    plan = QuestionTurnPlanner.plan(session_in_progress, runtime_decision_python)
    assert plan.allowed
    return plan


def _make_generated(
    text="What are Python decorators and how are they used?",
    topic_id="python",
):
    return GeneratedQuestion(
        question_text=text,
        question_type=QuestionType.INITIAL,
        topic_id=topic_id,
        difficulty=DifficultyLevel.MEDIUM,
    )


# ── A. Successful dispatch ────────────────────────────────────────────────────

def test_successful_dispatch_appends_history(session_in_progress, runtime_decision_python):
    plan = _get_plan(session_in_progress, runtime_decision_python)
    generated = _make_generated()
    assert len(session_in_progress.question_history) == 0

    record = QuestionDispatcher.dispatch(session_in_progress, plan, generated)

    assert len(session_in_progress.question_history) == 1
    assert session_in_progress.question_history[0] == record


# ── B. Global counter increments by exactly 1 ─────────────────────────────────

def test_global_counter_increments_by_one(session_in_progress, runtime_decision_python):
    plan = _get_plan(session_in_progress, runtime_decision_python)
    generated = _make_generated()
    before = session_in_progress.questions_asked_total

    QuestionDispatcher.dispatch(session_in_progress, plan, generated)

    assert session_in_progress.questions_asked_total == before + 1


# ── C. Topic counter increments by exactly 1 ─────────────────────────────────

def test_topic_counter_increments_by_one(session_in_progress, runtime_decision_python):
    plan = _get_plan(session_in_progress, runtime_decision_python)
    generated = _make_generated()
    topic_progress = session_in_progress.topic_progress[0]
    before = topic_progress.questions_asked

    QuestionDispatcher.dispatch(session_in_progress, plan, generated)

    assert topic_progress.questions_asked == before + 1


# ── D. InterviewState is NOT mutated ─────────────────────────────────────────

def test_interview_state_not_mutated(session_in_progress, runtime_decision_python):
    original_state = session_in_progress.state
    plan = _get_plan(session_in_progress, runtime_decision_python)
    QuestionDispatcher.dispatch(session_in_progress, plan, _make_generated())
    assert session_in_progress.state == original_state


# ── E. TopicState is NOT mutated ──────────────────────────────────────────────

def test_topic_state_not_mutated(session_in_progress, runtime_decision_python):
    original_topic_state = session_in_progress.topic_progress[0].state
    plan = _get_plan(session_in_progress, runtime_decision_python)
    QuestionDispatcher.dispatch(session_in_progress, plan, _make_generated())
    assert session_in_progress.topic_progress[0].state == original_topic_state


# ── F. qualitatively_covered is NOT mutated ──────────────────────────────────

def test_qualitatively_covered_not_mutated(session_in_progress, runtime_decision_python):
    """
    CRITICAL: Dispatching a question MUST NOT set qualitatively_covered=True.
    Qualitative coverage belongs to the future Answer Evaluation phase.
    """
    assert session_in_progress.topic_progress[0].qualitatively_covered is False
    plan = _get_plan(session_in_progress, runtime_decision_python)
    QuestionDispatcher.dispatch(session_in_progress, plan, _make_generated())
    assert session_in_progress.topic_progress[0].qualitatively_covered is False


# ── G. Counter drift detection ────────────────────────────────────────────────

def test_counter_drift_prevents_dispatch(session_in_progress, runtime_decision_python):
    """
    If questions_asked_total changed between plan creation and dispatch
    (e.g. concurrent call), the dispatcher must detect the drift and abort.
    """
    plan = _get_plan(session_in_progress, runtime_decision_python)
    # Simulate a concurrent question being dispatched
    session_in_progress.questions_asked_total += 1

    with pytest.raises(QuestionDispatchError, match="drift"):
        QuestionDispatcher.dispatch(session_in_progress, plan, _make_generated())


# ── H. Budget check prevents dispatch ────────────────────────────────────────

def test_budget_exhausted_prevents_dispatch(session_in_progress, runtime_decision_python):
    plan = _get_plan(session_in_progress, runtime_decision_python)
    # Exhaust budget manually after plan was created
    session_in_progress.questions_asked_total = session_in_progress.blueprint.total_question_budget

    # Either drift or budget check will fire — both are QuestionDispatchErrors
    with pytest.raises(QuestionDispatchError):
        QuestionDispatcher.dispatch(session_in_progress, plan, _make_generated())


# ── H2. Session must be IN_PROGRESS ──────────────────────────────────────────

def test_dispatch_fails_if_not_in_progress(session_in_progress, runtime_decision_python):
    plan = _get_plan(session_in_progress, runtime_decision_python)
    session_in_progress.state = InterviewState.COMPLETED

    with pytest.raises(QuestionDispatchError, match="IN_PROGRESS"):
        QuestionDispatcher.dispatch(session_in_progress, plan, _make_generated())


# ── I. Rollback on failure leaves session consistent ────────────────────────

def test_rollback_on_budget_failure_leaves_session_consistent(
    session_in_progress, runtime_decision_python
):
    plan = _get_plan(session_in_progress, runtime_decision_python)
    original_total = session_in_progress.questions_asked_total
    original_topic = session_in_progress.topic_progress[0].questions_asked
    original_history_len = len(session_in_progress.question_history)

    session_in_progress.questions_asked_total = session_in_progress.blueprint.total_question_budget

    try:
        QuestionDispatcher.dispatch(session_in_progress, plan, _make_generated())
    except QuestionDispatchError:
        pass

    # Session must be unchanged
    assert session_in_progress.questions_asked_total == session_in_progress.blueprint.total_question_budget
    assert session_in_progress.topic_progress[0].questions_asked == original_topic
    assert len(session_in_progress.question_history) == original_history_len


# ── J. QuestionRecord data correctness ───────────────────────────────────────

def test_question_record_contains_correct_data(session_in_progress, runtime_decision_python):
    plan = _get_plan(session_in_progress, runtime_decision_python)
    text = "How does Python's GIL affect multithreading?"
    generated = _make_generated(text=text)

    record = QuestionDispatcher.dispatch(session_in_progress, plan, generated)

    assert record.session_id == session_in_progress.session_id
    assert record.turn_number == 1  # first question
    assert record.topic_id == "python"
    assert record.question_text == text
    assert record.question_type == QuestionType.INITIAL
    assert record.difficulty == DifficultyLevel.MEDIUM


# ── Multiple sequential dispatches ───────────────────────────────────────────

def test_sequential_dispatches_increment_correctly(session_in_progress, runtime_decision_python):
    """Two sequential dispatches each increment by exactly 1."""
    plan1 = _get_plan(session_in_progress, runtime_decision_python)
    QuestionDispatcher.dispatch(session_in_progress, plan1, _make_generated("Q1 about Python?"))

    # Rebuild plan for second question
    plan2 = _get_plan(session_in_progress, runtime_decision_python)
    QuestionDispatcher.dispatch(session_in_progress, plan2, _make_generated("Q2 about Python decorators?"))

    assert session_in_progress.questions_asked_total == 2
    assert session_in_progress.topic_progress[0].questions_asked == 2
    assert len(session_in_progress.question_history) == 2
    assert session_in_progress.question_history[0].turn_number == 1
    assert session_in_progress.question_history[1].turn_number == 2
