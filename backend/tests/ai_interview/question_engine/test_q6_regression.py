"""
Regression test suite for Question 6 failure.

Root Cause:
    In session_creation_service.py, JobRequirementContext hardcoded
    interview_duration_minutes=30 and passed constraints=None to CoveragePlanner.
    CoveragePlanner calculated total_question_budget = max(1, duration // 5) = 6.
    Even though the campaign's strategy snapshot configured max_questions = 12,
    the blueprint was locked to 6.
    When a candidate answered question 6 (questions_asked_total == 6):
    - CompletionEngine (using strategy.max_questions = 12) authorized continuing
    - QuestionTurnPlanner (using blueprint.total_question_budget = 6) denied turn 7
      with TurnDenialReason.GLOBAL_QUESTION_BUDGET_EXHAUSTED
    - InterviewTurnCoordinator treated the denied turn as a generation failure
      and returned RuntimeAction.FAIL
    - Transport service marked the session FAILED with GENERATION_FAILED error.

Fix:
    In session_creation_service.py:
    1. Read strategy snapshot early. When strategy_def.max_questions > 0 and
       budget_mode != 'distinct_topics', pass
       PlanningConstraints(total_question_budget=strategy_def.max_questions).
    2. Extract duration_minutes from campaign settings (or default 30).
    3. In distinct_topics mode, sync blueprint.total_question_budget to match
       the resolved topic count.
"""
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from app.ai_interview.core.enums import (
    DifficultyLevel,
    InterviewState,
    QuestionType,
    TopicState,
    InterviewType,
    InterviewModeStatus,
)
from app.ai_interview.runtime.enums import RuntimeAction
from app.ai_interview.runtime.schemas import RuntimeDecision
from app.ai_interview.schemas.blueprint import InterviewBlueprint, TopicBlueprint
from app.ai_interview.schemas.session import InterviewSessionSchema, TopicProgress
from app.ai_interview.schemas.interview_mode import (
    InterviewModeDefinition,
    InterviewModeSettings,
)
from app.ai_interview.schemas.strategy import (
    StrategyDefinition,
    CompanyOverrideBounds,
    FollowUpPolicy,
)
from app.ai_interview.question_engine.enums import (
    TurnDenialReason,
    QuestionEngineFailureCode,
    QuestionStatus,
)
from app.ai_interview.question_engine.question_turn_planner import QuestionTurnPlanner
from app.ai_interview.question_engine.question_engine import QuestionEngine
from app.ai_interview.question_engine.question_generator import FakeQuestionGenerator
from app.ai_interview.answer_engine.answer_engine import AnswerEngine
from app.ai_interview.answer_engine.schemas import AnswerSubmission, EvaluationResult
from app.ai_interview.orchestration.interview_turn_coordinator import InterviewTurnCoordinator
from app.ai_interview.resume_processing.schemas import (
    CandidateInterviewContext,
    ExtractionMetadata,
)
from app.ai_interview.resume_processing.enums import ExtractionQualityStatus
from app.ai_interview.schemas.resume import (
    StructuredResume,
    Skill,
)
from app.ai_interview.transport.services.session_creation_service import SessionCreationService
from app.auth.jwt_handler import TokenPayload


# ── Helpers ───────────────────────────────────────────────────────────────────

def _build_context() -> CandidateInterviewContext:
    return CandidateInterviewContext(
        candidate_id="cand-001",
        structured_resume=StructuredResume(
            skills=[Skill(name="Python", category="Language", proficiency="Advanced")]
        ),
        extraction_metadata=ExtractionMetadata(
            source_type="pdf",
            extractor_name="test",
            extractor_version="1.0",
            character_count=500,
            detected_sections=["skills"],
            warning_count=0,
            processing_duration_ms=50.0,
        ),
        quality_status=ExtractionQualityStatus.USABLE,
    )


def _build_mode() -> InterviewModeDefinition:
    return InterviewModeDefinition(
        mode_id="official-standard",
        version=1,
        name="Official Standard",
        description="Standard technical interview mode",
        status=InterviewModeStatus.PUBLISHED,
        settings=InterviewModeSettings(
            allowed_question_types=["initial", "follow_up"],
            max_turns=20,
        ),
        created_at=datetime.utcnow(),
    )


def _build_strategy_def(max_questions: int = 12) -> StrategyDefinition:
    return StrategyDefinition(
        strategy_id="balanced-v1",
        name="Balanced",
        description="Balanced interview strategy with dynamic follow-ups.",
        version=1,
        is_active=True,
        applicable_interview_types=[InterviewType.TECHNICAL],
        budget_mode="fixed",
        min_questions=6,
        target_questions=max_questions,
        max_questions=max_questions,
        max_questions_per_topic=3,
        max_followups_per_topic=2,
        strong_threshold=0.8,
        acceptable_threshold=0.6,
        weak_threshold=0.4,
        company_override_bounds=CompanyOverrideBounds(
            target_questions_min_delta=-2,
            target_questions_max_delta=2,
            allowed_difficulty_bands=[DifficultyLevel.MEDIUM],
        ),
        followup_policy=FollowUpPolicy(
            max_per_topic=2,
        ),
    )


def _build_multi_topic_blueprint(total_budget: int) -> InterviewBlueprint:
    topics = [
        TopicBlueprint(
            topic_id=f"topic_{i}",
            topic_name=f"Topic {i}",
            source="required_skill",
            priority=10 - i,
            mandatory=True,
            initial_difficulty=DifficultyLevel.MEDIUM,
            allowed_question_types=[QuestionType.INITIAL, QuestionType.FOLLOW_UP],
            question_budget=3,
        )
        for i in range(1, 6)
    ]
    return InterviewBlueprint(
        blueprint_version="1.0",
        total_question_budget=total_budget,
        min_questions=3,
        max_questions=total_budget,
        emergency_max_questions=total_budget + 2,
        topics=topics,
    )


def _build_session(blueprint: InterviewBlueprint, strategy_def: StrategyDefinition) -> InterviewSessionSchema:
    return InterviewSessionSchema(
        session_id="session-q6-test",
        candidate_id="cand-001",
        company_id="comp-001",
        campaign_id="camp-001",
        mode_id="official-standard",
        mode_version=1,
        state=InterviewState.IN_PROGRESS,
        blueprint=blueprint,
        questions_asked_total=0,
        current_topic_id=blueprint.topics[0].topic_id,
        topic_progress=[
            TopicProgress(topic_id=tb.topic_id, state=TopicState.NOT_STARTED, questions_asked=0)
            for tb in blueprint.topics
        ],
        strategy_snapshot=strategy_def,
        created_at=datetime.utcnow(),
    )


# ── Test 1: Bug Reproduction ─────────────────────────────────────────────────

def test_q6_bug_reproduction_denies_turn_7_with_budget_6():
    """
    Demonstrates the bug: when total_question_budget is 6,
    attempting turn 7 (after 6 questions are asked) is denied.
    """
    blueprint = _build_multi_topic_blueprint(total_budget=6)
    strategy = _build_strategy_def(max_questions=12)
    session = _build_session(blueprint, strategy)

    # Simulate 6 questions asked
    session.questions_asked_total = 6
    session.topic_progress[0].questions_asked = 2
    session.topic_progress[1].questions_asked = 2
    session.topic_progress[2].questions_asked = 2
    session.current_topic_id = "topic_4"
    session.topic_progress[3].state = TopicState.IN_PROGRESS

    decision = RuntimeDecision(
        session_id=session.session_id,
        current_state=InterviewState.IN_PROGRESS,
        allowed_action=RuntimeAction.NO_ACTION,
        active_topic_id="topic_4",
        current_difficulty=DifficultyLevel.MEDIUM,
        should_complete=False,
    )

    plan = QuestionTurnPlanner.plan(session, decision)
    assert not plan.allowed
    assert plan.denial_reason == TurnDenialReason.GLOBAL_BUDGET_EXHAUSTED


# ── Test 2: Fix Verification — QuestionTurnPlanner allows turn 7+ ─────────────

def test_q6_fixed_budget_allows_question_7_and_beyond():
    """
    When total_question_budget is aligned with strategy max_questions (12),
    QuestionTurnPlanner allows question 7, 8, etc.
    """
    blueprint = _build_multi_topic_blueprint(total_budget=12)
    strategy = _build_strategy_def(max_questions=12)
    session = _build_session(blueprint, strategy)

    # 6 questions asked so far
    session.questions_asked_total = 6
    session.topic_progress[0].questions_asked = 2
    session.topic_progress[1].questions_asked = 2
    session.topic_progress[2].questions_asked = 2
    session.current_topic_id = "topic_4"
    session.topic_progress[3].state = TopicState.IN_PROGRESS

    decision = RuntimeDecision(
        session_id=session.session_id,
        current_state=InterviewState.IN_PROGRESS,
        allowed_action=RuntimeAction.NO_ACTION,
        active_topic_id="topic_4",
        current_difficulty=DifficultyLevel.MEDIUM,
        should_complete=False,
    )

    plan = QuestionTurnPlanner.plan(session, decision)
    assert plan.allowed is True
    assert plan.denial_reason is None
    assert plan.turn_number == 7


# ── Test 3: Full QuestionEngine dispatch beyond Question 6 ───────────────────

def test_question_engine_dispatches_question_7_and_8():
    """
    QuestionEngine generates, validates, and dispatches question 7 and 8
    without any budget exhaustion error.
    """
    blueprint = _build_multi_topic_blueprint(total_budget=12)
    strategy = _build_strategy_def(max_questions=12)
    session = _build_session(blueprint, strategy)
    context = _build_context()
    mode = _build_mode()

    # Pre-populate 6 questions in history
    session.questions_asked_total = 6
    session.current_topic_id = "topic_3"
    session.topic_progress[2].state = TopicState.IN_PROGRESS
    session.topic_progress[2].questions_asked = 0

    engine = QuestionEngine(generator=FakeQuestionGenerator(mode="valid"))
    decision = RuntimeDecision(
        session_id=session.session_id,
        current_state=InterviewState.IN_PROGRESS,
        allowed_action=RuntimeAction.NO_ACTION,
        active_topic_id="topic_3",
        current_difficulty=DifficultyLevel.MEDIUM,
        should_complete=False,
    )

    # Dispatch Question 7
    result_q7 = engine.request_next_question(session, decision, context, mode)
    assert result_q7.success is True
    assert result_q7.question_record.turn_number == 7
    assert session.questions_asked_total == 7

    # Dispatch Question 8
    result_q8 = engine.request_next_question(session, decision, context, mode)
    assert result_q8.success is True
    assert result_q8.question_record.turn_number == 8
    assert session.questions_asked_total == 8


# ── Test 4: InterviewTurnCoordinator progression past Turn 6 ─────────────────

def test_coordinator_advances_beyond_question_6_without_failure():
    """
    InterviewTurnCoordinator handles answer submission for question 6 and
    generates question 7 with RuntimeAction.NO_ACTION (not RuntimeAction.FAIL).
    """
    blueprint = _build_multi_topic_blueprint(total_budget=12)
    strategy = _build_strategy_def(max_questions=12)
    session = _build_session(blueprint, strategy)
    context = _build_context()
    mode = _build_mode()

    from app.ai_interview.question_engine.schemas import QuestionRecord
    q6_record = QuestionRecord(
        record_id="q6-rec",
        session_id=session.session_id,
        turn_number=6,
        topic_id="topic_2",
        question_text="Tell me about SQL indexing.",
        question_type=QuestionType.INITIAL,
        difficulty=DifficultyLevel.MEDIUM,
        status=QuestionStatus.DISPATCHED,
    )
    session.question_history.append(q6_record)
    session.questions_asked_total = 6
    session.current_topic_id = "topic_2"
    session.topic_progress[1].state = TopicState.IN_PROGRESS
    session.topic_progress[1].questions_asked = 2

    # Mock answer engine evaluation
    from app.ai_interview.answer_engine.enums import FollowUpSignal, CoverageSignal
    mock_answer_engine = MagicMock(spec=AnswerEngine)
    mock_eval = MagicMock()
    mock_eval.topic_id = "topic_2"
    mock_eval.overall_score = 85
    mock_eval.follow_up_signal = FollowUpSignal.NONE
    mock_eval.qualitative_coverage_signal = CoverageSignal.QUALITATIVELY_COVERED
    mock_answer_engine.evaluate_answer.return_value = mock_eval

    question_engine = QuestionEngine(generator=FakeQuestionGenerator(mode="valid"))

    coordinator = InterviewTurnCoordinator(
        question_engine=question_engine,
        answer_engine=mock_answer_engine,
    )

    submission = AnswerSubmission(
        session_id=session.session_id,
        question_record_id="q6-rec",
        answer_text="B-tree indexes provide logarithmic lookup time.",
    )

    turn_result = coordinator.advance_interview(session, context, mode, submission)

    assert turn_result.action != RuntimeAction.FAIL, "Turn coordinator returned FAIL at turn 7!"
    assert turn_result.interview_completed is False
    assert turn_result.question is not None
    assert turn_result.question.turn_number == 7
    assert session.questions_asked_total == 7


# ── Test 5: SessionCreationService sets budget from strategy max_questions ──

@pytest.mark.asyncio
async def test_session_creation_service_sets_correct_budget_from_strategy():
    """
    SessionCreationService derives blueprint total_question_budget from
    strategy_def.max_questions (12) rather than hardcoded 30 // 5 = 6.
    """
    strategy_dict = _build_strategy_def(max_questions=12).model_dump(mode="json")
    campaign = {
        "_id": "camp-test-12",
        "name": "Senior Python Engineer",
        "role_target": "Senior Python Engineer",
        "department": "Engineering",
        "status": "active",
        "company_id": "comp-test-12",
        "interview_mode": "m1",
        "interview_type": "technical",
        "requirements": [{"skill": "Python", "criticality": "required"}],
        "strategy_snapshot": {
            "snapshot_id": "snap-12",
            "definition": strategy_dict,
        },
        "settings": {
            "duration_minutes": 45,
        },
    }
    candidate = {
        "_id": "cand-test-12",
        "name": "Test Candidate",
        "email": "cand@test.com",
        "target_role": "Senior Python Engineer",
        "experience_level": "senior",
        "campaign_id": "camp-test-12",
    }
    token = TokenPayload(
        sub="cand-test-12",
        role="candidate",
        company_id="comp-test-12",
        candidate_id="cand-test-12",
        exp=9999999999,
        iat=1,
    )

    mock_repos = {
        "campaign_repo": AsyncMock(),
        "mode_repo": AsyncMock(),
        "resume_repo": AsyncMock(),
        "candidate_repo": AsyncMock(),
        "session_repo": AsyncMock(),
    }
    mock_repos["campaign_repo"].get_by_id.return_value = campaign
    mock_repos["candidate_repo"].get.return_value = candidate
    mock_repos["candidate_repo"].get_by_id.return_value = candidate
    mock_repos["resume_repo"].get_by_candidate.return_value = {"id": "r1"}
    mock_repos["mode_repo"].get_by_mode_id.return_value = {
        "mode_id": "m1", "version": 1, "name": "mode", "description": "desc",
        "status": "published", "created_at": "2024-01-01T00:00:00Z", "settings": {},
    }
    mock_repos["session_repo"].find_active_session.return_value = None

    service = SessionCreationService(**mock_repos)
    await service.create_session(token, "camp-test-12")

    saved_session = mock_repos["session_repo"].save.call_args[0][0]
    assert saved_session.blueprint.total_question_budget == 12, (
        f"Expected total_question_budget == 12, got {saved_session.blueprint.total_question_budget}"
    )
    assert saved_session.blueprint.max_questions == 12


# ── Test 6: Campaign duration honored when strategy is absent ────────────────

@pytest.mark.asyncio
async def test_session_creation_honors_campaign_duration_without_strategy():
    """
    When no strategy snapshot is present, campaign duration (e.g. 60 min)
    is used to calculate total_question_budget = 60 // 5 = 12 (not hardcoded 30 -> 6).
    """
    campaign = {
        "_id": "camp-test-duration",
        "name": "General Tech Drive",
        "role_target": "Software Engineer",
        "department": "Engineering",
        "status": "active",
        "company_id": "comp-test-dur",
        "interview_mode": "m1",
        "requirements": [{"skill": "Python", "criticality": "required"}],
        "settings": {
            "duration_minutes": 60,
        },
    }
    candidate = {
        "_id": "cand-test-dur",
        "name": "Duration Candidate",
        "email": "dur@test.com",
        "target_role": "Software Engineer",
        "campaign_id": "camp-test-duration",
    }
    token = TokenPayload(
        sub="cand-test-dur",
        role="candidate",
        company_id="comp-test-dur",
        candidate_id="cand-test-dur",
        exp=9999999999,
        iat=1,
    )

    mock_repos = {
        "campaign_repo": AsyncMock(),
        "mode_repo": AsyncMock(),
        "resume_repo": AsyncMock(),
        "candidate_repo": AsyncMock(),
        "session_repo": AsyncMock(),
    }
    mock_repos["campaign_repo"].get_by_id.return_value = campaign
    mock_repos["candidate_repo"].get.return_value = candidate
    mock_repos["candidate_repo"].get_by_id.return_value = candidate
    mock_repos["resume_repo"].get_by_candidate.return_value = {"id": "r1"}
    mock_repos["mode_repo"].get_by_mode_id.return_value = {
        "mode_id": "m1", "version": 1, "name": "mode", "description": "desc",
        "status": "published", "created_at": "2024-01-01T00:00:00Z", "settings": {},
    }
    mock_repos["session_repo"].find_active_session.return_value = None

    service = SessionCreationService(**mock_repos)
    await service.create_session(token, "camp-test-duration")

    saved_session = mock_repos["session_repo"].save.call_args[0][0]
    assert saved_session.blueprint.total_question_budget == 12
    assert saved_session.blueprint.max_questions == 12


# ── Test 7: Correct denial at real maximum ───────────────────────────────────

def test_correct_denial_at_real_strategy_maximum():
    """
    When questions_asked_total reaches the real maximum (12),
    QuestionTurnPlanner properly denies with GLOBAL_QUESTION_BUDGET_EXHAUSTED.
    """
    blueprint = _build_multi_topic_blueprint(total_budget=12)
    strategy = _build_strategy_def(max_questions=12)
    session = _build_session(blueprint, strategy)

    session.questions_asked_total = 12
    session.current_topic_id = "topic_5"
    session.topic_progress[4].state = TopicState.IN_PROGRESS
    session.topic_progress[4].questions_asked = 1

    decision = RuntimeDecision(
        session_id=session.session_id,
        current_state=InterviewState.IN_PROGRESS,
        allowed_action=RuntimeAction.NO_ACTION,
        active_topic_id="topic_5",
        current_difficulty=DifficultyLevel.MEDIUM,
        should_complete=False,
    )

    plan = QuestionTurnPlanner.plan(session, decision)
    assert plan.allowed is False
    assert plan.denial_reason == TurnDenialReason.GLOBAL_BUDGET_EXHAUSTED


# ── Test 8: Breadth Screening distinct_topics sync allows turn 7+ ─────────────

@pytest.mark.asyncio
async def test_distinct_topics_budget_sync_allows_progression_beyond_6():
    """
    In Breadth Screening (budget_mode='distinct_topics'), 8 topics resolve
    blueprint total_question_budget to 8 (not stuck at duration 30 // 5 = 6).
    Turn 7 is allowed.
    """
    from app.ai_interview.blueprint_planning.schemas import BlueprintPlanningRequest
    from app.ai_interview.schemas.blueprint import InterviewBlueprint, TopicBlueprint

    breadth_def = {
        "strategy_id": "breadth_screening",
        "name": "Breadth Screening",
        "description": "Breadth screening across distinct topics.",
        "version": 1,
        "is_active": True,
        "applicable_interview_types": ["technical"],
        "budget_mode": "distinct_topics",
        "min_questions": 0,
        "target_questions": 0,
        "max_questions": 0,
        "max_questions_per_topic": 1,
        "max_followups_per_topic": 1,
        "strong_threshold": 0.8,
        "acceptable_threshold": 0.6,
        "weak_threshold": 0.4,
    }

    campaign = {
        "_id": "camp-test-breadth",
        "name": "Breadth Drive",
        "role_target": "General Engineer",
        "department": "Engineering",
        "status": "active",
        "company_id": "comp-breadth",
        "interview_mode": "m1",
        "interview_type": "technical",
        "requirements": [{"skill": f"Skill_{i}", "criticality": "required"} for i in range(8)],
        "strategy_snapshot": {
            "snapshot_id": "snap-breadth",
            "definition": breadth_def,
        },
    }
    candidate = {
        "_id": "cand-breadth",
        "name": "Breadth Candidate",
        "email": "breadth@test.com",
        "target_role": "General Engineer",
        "campaign_id": "camp-test-breadth",
    }
    token = TokenPayload(
        sub="cand-breadth",
        role="candidate",
        company_id="comp-breadth",
        candidate_id="cand-breadth",
        exp=9999999999,
        iat=1,
    )

    mock_repos = {
        "campaign_repo": AsyncMock(),
        "mode_repo": AsyncMock(),
        "resume_repo": AsyncMock(),
        "candidate_repo": AsyncMock(),
        "session_repo": AsyncMock(),
    }
    mock_repos["campaign_repo"].get_by_id.return_value = campaign
    mock_repos["candidate_repo"].get.return_value = candidate
    mock_repos["candidate_repo"].get_by_id.return_value = candidate
    mock_repos["resume_repo"].get_by_candidate.return_value = {"id": "r1"}
    mock_repos["mode_repo"].get_by_mode_id.return_value = {
        "mode_id": "m1", "version": 1, "name": "mode", "description": "desc",
        "status": "published", "created_at": "2024-01-01T00:00:00Z", "settings": {},
    }
    mock_repos["session_repo"].find_active_session.return_value = None

    eight_topics = [
        TopicBlueprint(
            topic_id=f"top_{i}", topic_name=f"Topic {i}", source="req",
            priority=1, initial_difficulty=DifficultyLevel.MEDIUM,
            allowed_question_types=[QuestionType.INITIAL], question_budget=1,
        )
        for i in range(8)
    ]
    mock_bp = InterviewBlueprint(
        blueprint_version="1.0", min_questions=1, max_questions=6,
        total_question_budget=6, emergency_max_questions=8, topics=eight_topics,
    )

    service = SessionCreationService(**mock_repos)
    with patch.object(service.planner, "plan", return_value=mock_bp):
        await service.create_session(token, "camp-test-breadth")

    saved_session = mock_repos["session_repo"].save.call_args[0][0]

    # Blueprint budget must have been raised to 8 to match topic count
    assert saved_session.blueprint.total_question_budget == 8
    assert saved_session.blueprint.max_questions == 8
    assert saved_session.strategy_snapshot.max_questions == 8

    # Now verify Turn 7 is permitted with 6 questions asked
    saved_session.state = InterviewState.IN_PROGRESS
    saved_session.questions_asked_total = 6
    saved_session.current_topic_id = "top_6"
    saved_session.topic_progress[6].state = TopicState.IN_PROGRESS

    decision = RuntimeDecision(
        session_id=saved_session.session_id,
        current_state=InterviewState.IN_PROGRESS,
        allowed_action=RuntimeAction.NO_ACTION,
        active_topic_id="top_6",
        current_difficulty=DifficultyLevel.MEDIUM,
        should_complete=False,
    )

    plan = QuestionTurnPlanner.plan(saved_session, decision)
    assert plan.allowed is True
    assert plan.denial_reason is None
    assert plan.turn_number == 7
