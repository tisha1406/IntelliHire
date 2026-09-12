"""
Tests for QuestionTurnPlanner.

Verifies deterministic permission logic for all cases:
  A. Valid turn creation
  B. Invalid interview state
  C. Runtime decision does not authorize question
  D. Global budget exhausted
  E. Topic budget exhausted
  F. Missing active topic
  G. Deterministic turn numbering
"""
import pytest
from datetime import datetime

from app.ai_interview.core.enums import InterviewState, DifficultyLevel, QuestionType, TopicState
from app.ai_interview.runtime.enums import RuntimeAction
from app.ai_interview.runtime.schemas import RuntimeDecision
from app.ai_interview.schemas.session import InterviewSessionSchema, TopicProgress
from app.ai_interview.question_engine.question_turn_planner import QuestionTurnPlanner
from app.ai_interview.question_engine.enums import TurnDenialReason


# ── A. Valid turn creation ─────────────────────────────────────────────────────

def test_valid_turn_plan(session_in_progress, blueprint, runtime_decision_python):
    plan = QuestionTurnPlanner.plan(session_in_progress, runtime_decision_python)

    assert plan.allowed is True
    assert plan.denial_reason is None
    assert plan.topic_id == "python"
    assert plan.topic_name == "Python"
    assert plan.difficulty == DifficultyLevel.MEDIUM
    assert plan.turn_number == 1  # questions_asked_total=0, so turn=1
    assert plan.topic_question_budget == 3
    assert plan.topic_questions_asked == 0
    assert plan.total_question_budget == 5
    assert plan.total_questions_asked == 0
    assert QuestionType.INITIAL in plan.allowed_question_types


# ── B. Invalid interview state ─────────────────────────────────────────────────

@pytest.mark.parametrize("state", [
    InterviewState.CREATED,
    InterviewState.INITIALIZING,
    InterviewState.PAUSED,
    InterviewState.COMPLETED,
    InterviewState.FAILED,
])
def test_denied_when_not_in_progress(session_in_progress, runtime_decision_python, state):
    session_in_progress.state = state
    plan = QuestionTurnPlanner.plan(session_in_progress, runtime_decision_python)

    assert plan.allowed is False
    assert plan.denial_reason == TurnDenialReason.INTERVIEW_NOT_IN_PROGRESS


# ── C. Runtime decision does not authorize ─────────────────────────────────────

def test_denied_when_runtime_says_complete(session_in_progress, blueprint):
    decision = RuntimeDecision(
        current_state=InterviewState.IN_PROGRESS,
        allowed_action=RuntimeAction.COMPLETE,
        active_topic_id="python",
        should_complete=True,
    )
    plan = QuestionTurnPlanner.plan(session_in_progress, decision)
    assert plan.allowed is False
    assert plan.denial_reason == TurnDenialReason.RUNTIME_DOES_NOT_AUTHORIZE


def test_denied_when_no_active_topic_in_decision(session_in_progress):
    decision = RuntimeDecision(
        current_state=InterviewState.IN_PROGRESS,
        allowed_action=RuntimeAction.NO_ACTION,
        active_topic_id=None,
        should_complete=False,
    )
    plan = QuestionTurnPlanner.plan(session_in_progress, decision)
    assert plan.allowed is False
    assert plan.denial_reason == TurnDenialReason.RUNTIME_DOES_NOT_AUTHORIZE


# ── D. Global budget exhausted ────────────────────────────────────────────────

def test_denied_when_global_budget_exhausted(session_in_progress, runtime_decision_python):
    session_in_progress.questions_asked_total = 5  # == blueprint.total_question_budget
    plan = QuestionTurnPlanner.plan(session_in_progress, runtime_decision_python)

    assert plan.allowed is False
    assert plan.denial_reason == TurnDenialReason.GLOBAL_BUDGET_EXHAUSTED


def test_denied_when_global_budget_exceeded(session_in_progress, runtime_decision_python):
    session_in_progress.questions_asked_total = 10
    plan = QuestionTurnPlanner.plan(session_in_progress, runtime_decision_python)

    assert plan.allowed is False
    assert plan.denial_reason == TurnDenialReason.GLOBAL_BUDGET_EXHAUSTED


# ── E. Topic budget exhausted ─────────────────────────────────────────────────

def test_denied_when_topic_budget_exhausted(session_in_progress, runtime_decision_python):
    # python topic has budget=3; simulate 3 questions already asked
    session_in_progress.topic_progress[0].questions_asked = 3
    session_in_progress.questions_asked_total = 3  # consistent with topic count

    plan = QuestionTurnPlanner.plan(session_in_progress, runtime_decision_python)

    assert plan.allowed is False
    assert plan.denial_reason == TurnDenialReason.TOPIC_BUDGET_EXHAUSTED


def test_allowed_when_topic_budget_not_yet_exhausted(session_in_progress, runtime_decision_python):
    # 2 asked out of 3 budget — still allowed
    session_in_progress.topic_progress[0].questions_asked = 2
    session_in_progress.questions_asked_total = 2

    plan = QuestionTurnPlanner.plan(session_in_progress, runtime_decision_python)

    assert plan.allowed is True
    assert plan.topic_questions_asked == 2


# ── F. Topic not found in blueprint ───────────────────────────────────────────

def test_denied_when_topic_not_in_blueprint(session_in_progress):
    decision = RuntimeDecision(
        current_state=InterviewState.IN_PROGRESS,
        allowed_action=RuntimeAction.NO_ACTION,
        active_topic_id="unknown-topic-xyz",
        should_complete=False,
    )
    session_in_progress.state = InterviewState.IN_PROGRESS
    plan = QuestionTurnPlanner.plan(session_in_progress, decision)

    assert plan.allowed is False
    assert plan.denial_reason == TurnDenialReason.TOPIC_NOT_FOUND_IN_BLUEPRINT


# ── G. Deterministic turn numbering ───────────────────────────────────────────

def test_turn_number_is_questions_asked_plus_one(session_in_progress, runtime_decision_python):
    session_in_progress.questions_asked_total = 0
    plan = QuestionTurnPlanner.plan(session_in_progress, runtime_decision_python)
    assert plan.turn_number == 1

    session_in_progress.questions_asked_total = 3
    # Reduce topic budget check interference
    session_in_progress.topic_progress[0].questions_asked = 3
    # Now topic budget exhausted — verify the turn_number is still 4 in the denied plan
    plan2 = QuestionTurnPlanner.plan(session_in_progress, runtime_decision_python)
    assert plan2.allowed is False
    assert plan2.turn_number == 4  # denial plan still reflects correct turn number


def test_planner_does_not_mutate_session(session_in_progress, runtime_decision_python):
    """Planner is a pure function — session state must be unchanged after call."""
    original_total = session_in_progress.questions_asked_total
    original_topic_count = session_in_progress.topic_progress[0].questions_asked
    original_state = session_in_progress.state

    QuestionTurnPlanner.plan(session_in_progress, runtime_decision_python)

    assert session_in_progress.questions_asked_total == original_total
    assert session_in_progress.topic_progress[0].questions_asked == original_topic_count
    assert session_in_progress.state == original_state


# ── Determinism ────────────────────────────────────────────────────────────────

def test_planner_is_deterministic(session_in_progress, runtime_decision_python):
    """Same inputs → same plan every time."""
    plan1 = QuestionTurnPlanner.plan(session_in_progress, runtime_decision_python)
    plan2 = QuestionTurnPlanner.plan(session_in_progress, runtime_decision_python)

    assert plan1.allowed == plan2.allowed
    assert plan1.turn_number == plan2.turn_number
    assert plan1.topic_id == plan2.topic_id
    assert plan1.difficulty == plan2.difficulty
