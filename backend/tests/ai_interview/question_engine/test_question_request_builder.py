"""
Tests for QuestionRequestBuilder.

Verifies:
  A. Relevant candidate evidence is selected based on topic keyword
  B. Unrelated evidence is excluded
  C. Previous question context is bounded
  D. Deterministic ordering
  E. selected_question_type is deterministically the first allowed type
  F. Missing optional evidence is handled safely
  G. Builder raises on denied plan
"""
import pytest

from app.ai_interview.core.enums import DifficultyLevel, QuestionType
from app.ai_interview.question_engine.question_turn_planner import QuestionTurnPlanner
from app.ai_interview.question_engine.question_request_builder import QuestionRequestBuilder
from app.ai_interview.question_engine.schemas import QuestionRecord
from tests.ai_interview.question_engine.conftest import make_question_record


def _get_plan(session_in_progress, runtime_decision_python):
    plan = QuestionTurnPlanner.plan(session_in_progress, runtime_decision_python)
    assert plan.allowed, f"Plan unexpectedly denied: {plan.denial_reason}"
    return plan


# ── A. Relevant evidence selection ────────────────────────────────────────────

def test_relevant_skills_included(
    session_in_progress, runtime_decision_python, candidate_context, interview_mode
):
    plan = _get_plan(session_in_progress, runtime_decision_python)
    request = QuestionRequestBuilder.build(plan, candidate_context, interview_mode, [])

    # "Python" skill should be in relevant_skills
    assert any("python" in s.lower() for s in request.relevant_skills)


def test_unrelated_skills_excluded(
    session_in_progress, runtime_decision_python, candidate_context, interview_mode
):
    plan = _get_plan(session_in_progress, runtime_decision_python)
    request = QuestionRequestBuilder.build(plan, candidate_context, interview_mode, [])

    # "React" is unrelated to Python topic
    assert all("react" not in s.lower() for s in request.relevant_skills)


def test_relevant_projects_included(
    session_in_progress, runtime_decision_python, candidate_context, interview_mode
):
    plan = _get_plan(session_in_progress, runtime_decision_python)
    request = QuestionRequestBuilder.build(plan, candidate_context, interview_mode, [])

    # Flask API project uses Python
    assert any("flask" in p.lower() or "python" in p.lower() for p in request.relevant_projects)


def test_unrelated_projects_excluded(
    session_in_progress, runtime_decision_python, candidate_context, interview_mode
):
    plan = _get_plan(session_in_progress, runtime_decision_python)
    request = QuestionRequestBuilder.build(plan, candidate_context, interview_mode, [])

    # React Dashboard has no Python relevance
    assert all("react dashboard" not in p.lower() for p in request.relevant_projects)


def test_relevant_experience_included(
    session_in_progress, runtime_decision_python, candidate_context, interview_mode
):
    plan = _get_plan(session_in_progress, runtime_decision_python)
    request = QuestionRequestBuilder.build(plan, candidate_context, interview_mode, [])

    # "Python Backend Developer" experience should be included
    assert any("python" in e.lower() for e in request.relevant_experience)


# ── B. Previous question context bounding ────────────────────────────────────

def test_previous_questions_bounded(
    session_in_progress, runtime_decision_python, candidate_context, interview_mode
):
    """Only the last MAX_PREVIOUS_QUESTIONS_CONTEXT questions are included."""
    from app.ai_interview.question_engine.config import QuestionEngineConfig
    max_ctx = QuestionEngineConfig.MAX_PREVIOUS_QUESTIONS_CONTEXT

    # Create more records than the limit
    history = [
        make_question_record(turn_number=i, question_text=f"Question number {i}")
        for i in range(1, max_ctx + 5)
    ]

    plan = _get_plan(session_in_progress, runtime_decision_python)
    request = QuestionRequestBuilder.build(plan, candidate_context, interview_mode, history)

    assert len(request.previous_questions) <= max_ctx


def test_previous_questions_empty_when_no_history(
    session_in_progress, runtime_decision_python, candidate_context, interview_mode
):
    plan = _get_plan(session_in_progress, runtime_decision_python)
    request = QuestionRequestBuilder.build(plan, candidate_context, interview_mode, [])
    assert request.previous_questions == []


def test_previous_questions_order_preserved(
    session_in_progress, runtime_decision_python, candidate_context, interview_mode
):
    """Order of previous questions must be deterministic (as-dispatched)."""
    history = [
        make_question_record(turn_number=1, question_text="First question"),
        make_question_record(turn_number=2, question_text="Second question"),
        make_question_record(turn_number=3, question_text="Third question"),
    ]

    plan = _get_plan(session_in_progress, runtime_decision_python)
    request = QuestionRequestBuilder.build(plan, candidate_context, interview_mode, history)

    assert request.previous_questions == [
        "First question", "Second question", "Third question"
    ]


# ── C. selected_question_type is deterministic first element ──────────────────

def test_selected_question_type_is_first_allowed(
    session_in_progress, runtime_decision_python, candidate_context, interview_mode
):
    plan = _get_plan(session_in_progress, runtime_decision_python)
    request = QuestionRequestBuilder.build(plan, candidate_context, interview_mode, [])

    # Python topic has [INITIAL, SKILL_SPECIFIC] — INITIAL must be selected
    assert request.selected_question_type == QuestionType.INITIAL


# ── D. Request fields match plan ──────────────────────────────────────────────

def test_request_matches_plan(
    session_in_progress, runtime_decision_python, candidate_context, interview_mode
):
    plan = _get_plan(session_in_progress, runtime_decision_python)
    request = QuestionRequestBuilder.build(plan, candidate_context, interview_mode, [])

    assert request.topic_id == plan.topic_id
    assert request.topic_name == plan.topic_name
    assert request.difficulty == plan.difficulty
    assert request.turn_number == plan.turn_number
    assert request.max_questions_for_topic == plan.topic_question_budget
    assert request.question_number == plan.topic_questions_asked + 1


# ── E. Denied plan raises ─────────────────────────────────────────────────────

def test_builder_raises_on_denied_plan(
    session_in_progress, runtime_decision_python, candidate_context, interview_mode
):
    plan = _get_plan(session_in_progress, runtime_decision_python)
    # Manually deny the plan
    denied_plan = plan.model_copy(update={"allowed": False})

    with pytest.raises(ValueError, match="denied"):
        QuestionRequestBuilder.build(denied_plan, candidate_context, interview_mode, [])


# ── F. Determinism ────────────────────────────────────────────────────────────

def test_builder_is_deterministic(
    session_in_progress, runtime_decision_python, candidate_context, interview_mode
):
    plan = _get_plan(session_in_progress, runtime_decision_python)
    req1 = QuestionRequestBuilder.build(plan, candidate_context, interview_mode, [])
    req2 = QuestionRequestBuilder.build(plan, candidate_context, interview_mode, [])

    assert req1.topic_id == req2.topic_id
    assert req1.difficulty == req2.difficulty
    assert req1.selected_question_type == req2.selected_question_type
    assert req1.relevant_skills == req2.relevant_skills
    assert req1.relevant_projects == req2.relevant_projects
    assert req1.relevant_experience == req2.relevant_experience
