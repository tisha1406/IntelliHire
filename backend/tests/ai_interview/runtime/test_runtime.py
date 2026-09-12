import pytest
from app.ai_interview.core.enums import InterviewState, TopicState, DifficultyLevel, DecisionReasonCode
from app.ai_interview.runtime import (
    RuntimeController, SessionInitializer, StateMachine, TopicStateManager,
    TopicProgressionEngine, CompletionEngine, RuntimeAction,
    IllegalStateTransitionError, SessionInitializationError
)
from app.ai_interview.schemas.blueprint import InterviewBlueprint, TopicBlueprint
from app.ai_interview.schemas.session import InterviewSessionSchema, TopicProgress

@pytest.fixture
def mock_blueprint():
    return InterviewBlueprint(
        blueprint_version="1.0",
        total_question_budget=5,
        min_questions=2,
        max_questions=5,
        emergency_max_questions=7,
        topics=[
            TopicBlueprint(topic_id="t1", topic_name="T1", source="SRC", priority=5, mandatory=True, initial_difficulty=DifficultyLevel.MEDIUM, allowed_question_types=[]),
            TopicBlueprint(topic_id="t2", topic_name="T2", source="SRC", priority=4, mandatory=True, initial_difficulty=DifficultyLevel.MEDIUM, allowed_question_types=[]),
            TopicBlueprint(topic_id="t3", topic_name="T3", source="SRC", priority=5, mandatory=False, initial_difficulty=DifficultyLevel.MEDIUM, allowed_question_types=[])
        ]
    )

def test_state_machine_legal_transitions():
    assert StateMachine.can_transition(InterviewState.CREATED, InterviewState.INITIALIZING) is True
    assert StateMachine.can_transition(InterviewState.IN_PROGRESS, InterviewState.PAUSED) is True
    assert StateMachine.can_transition(InterviewState.PAUSED, InterviewState.IN_PROGRESS) is True

def test_state_machine_illegal_transitions():
    assert StateMachine.can_transition(InterviewState.CREATED, InterviewState.PAUSED) is False
    with pytest.raises(IllegalStateTransitionError):
        StateMachine.assert_transition(InterviewState.COMPLETED, InterviewState.IN_PROGRESS)
    with pytest.raises(IllegalStateTransitionError):
        StateMachine.assert_transition(InterviewState.FAILED, InterviewState.PAUSED)

def test_session_initialization(mock_blueprint):
    session = SessionInitializer.initialize(
        blueprint=mock_blueprint, candidate_id="c1", company_id="c1", campaign_id="c1", mode_id="m1", mode_version=1
    )
    assert session.state == InterviewState.CREATED
    assert session.questions_asked_total == 0
    assert len(session.topic_progress) == 3
    # Check stable seeding
    assert session.topic_progress[0].topic_id == "t1"
    
    # Duplicate initialization check
    with pytest.raises(SessionInitializationError):
        # We simulate a bad blueprint just to test the error, but the immutability means
        # calling initialize on the same blueprint again returns a new isolated schema.
        SessionInitializer.initialize(blueprint=InterviewBlueprint(blueprint_version="1", total_question_budget=1, min_questions=1, max_questions=1, emergency_max_questions=1, topics=[mock_blueprint.topics[0], mock_blueprint.topics[0]]), candidate_id="c1", company_id="c1", campaign_id="c1", mode_id="m1", mode_version=1)

def test_topic_progression_ordering(mock_blueprint):
    session = SessionInitializer.initialize(
        blueprint=mock_blueprint, candidate_id="c1", company_id="c1", campaign_id="c1", mode_id="m1", mode_version=1
    )
    
    # T1 is Mandatory Pri 5, T2 is Mandatory Pri 4, T3 is Optional Pri 5
    next_topic = TopicProgressionEngine.get_next_active_topic(session)
    assert next_topic.topic_id == "t1"
    
    # Complete T1
    session.topic_progress[0].structurally_attempted = True
    session.topic_progress[0].qualitatively_covered = True
    TopicStateManager.attempt_cover(session.topic_progress[0])
    
    next_topic = TopicProgressionEngine.get_next_active_topic(session)
    assert next_topic.topic_id == "t2"
    
def test_failed_abandoned_semantics(mock_blueprint):
    session = SessionInitializer.initialize(
        blueprint=mock_blueprint, candidate_id="c1", company_id="c1", campaign_id="c1", mode_id="m1", mode_version=1
    )
    # Abandon T1
    TopicStateManager.mark_failed_abandoned(session.topic_progress[0])
    assert session.topic_progress[0].state == TopicState.FAILED_ABANDONED
    
    # T1 should not be selected again
    next_topic = TopicProgressionEngine.get_next_active_topic(session)
    assert next_topic.topic_id == "t2"
    
    # Check completion logic
    should_complete, trace = CompletionEngine.evaluate(session)
    # T2 is still unresolved mandatory, so should_complete = False
    assert should_complete is False
    
    # Complete T2
    session.topic_progress[1].structurally_attempted = True
    session.topic_progress[1].qualitatively_covered = True
    TopicStateManager.attempt_cover(session.topic_progress[1])
    
    should_complete, trace = CompletionEngine.evaluate(session)
    # All mandatory topics attempted (T1 abandoned, T2 covered)
    assert should_complete is True
    # But it must flag LOW_TOPIC_COVERAGE because T1 was abandoned
    assert DecisionReasonCode.LOW_TOPIC_COVERAGE in trace.reason_codes

def test_budget_exhaustion(mock_blueprint):
    session = SessionInitializer.initialize(
        blueprint=mock_blueprint, candidate_id="c1", company_id="c1", campaign_id="c1", mode_id="m1", mode_version=1
    )
    session.questions_asked_total = 6 # Exceeds budget 5
    
    should_complete, trace = CompletionEngine.evaluate(session)
    assert should_complete is True
    assert DecisionReasonCode.QUESTION_BUDGET_REACHED in trace.reason_codes
    assert trace.questions_asked_total == 6

def test_runtime_controller_flow(mock_blueprint):
    session = SessionInitializer.initialize(
        blueprint=mock_blueprint, candidate_id="c1", company_id="c1", campaign_id="c1", mode_id="m1", mode_version=1
    )
    
    decision = RuntimeController.get_allowed_action(session)
    assert decision.allowed_action == RuntimeAction.INITIALIZE
    RuntimeController.execute_transition(session, RuntimeAction.INITIALIZE)
    
    decision = RuntimeController.get_allowed_action(session)
    assert decision.allowed_action == RuntimeAction.START
    RuntimeController.execute_transition(session, RuntimeAction.START)
    
    # Now in progress
    decision = RuntimeController.get_allowed_action(session)
    assert decision.allowed_action == RuntimeAction.ADVANCE_TOPIC
    assert decision.active_topic_id == "t1"
    
    RuntimeController.execute_transition(session, RuntimeAction.ADVANCE_TOPIC)
    assert session.current_topic_id == "t1"
    
    # Pausing
    decision = RuntimeController.get_allowed_action(session)
    assert decision.allowed_action == RuntimeAction.NO_ACTION
    
    RuntimeController.execute_transition(session, RuntimeAction.PAUSE)
    decision = RuntimeController.get_allowed_action(session)
    assert decision.allowed_action == RuntimeAction.RESUME
