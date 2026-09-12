import pytest
from datetime import datetime
from app.ai_interview.schemas.session import InterviewSessionSchema, TopicProgress, TopicEvaluationAggregate
from app.ai_interview.schemas.blueprint import InterviewBlueprint, TopicBlueprint
from app.ai_interview.schemas.interview_mode import InterviewModeDefinition, InterviewModeSettings
from app.ai_interview.resume_processing.schemas import CandidateInterviewContext
from app.ai_interview.core.enums import InterviewState, TopicState, DifficultyLevel
from app.ai_interview.runtime.enums import RuntimeAction
from app.ai_interview.question_engine.question_engine import QuestionEngine
from app.ai_interview.question_engine.question_turn_planner import QuestionTurnPlanner
from app.ai_interview.question_engine.question_request_builder import QuestionRequestBuilder
from app.ai_interview.question_engine.question_generator import FakeQuestionGenerator
from app.ai_interview.question_engine.question_validator import QuestionValidator
from app.ai_interview.question_engine.duplicate_detector import DuplicateDetector
from app.ai_interview.question_engine.question_dispatcher import QuestionDispatcher
from app.ai_interview.answer_engine.answer_engine import AnswerEngine
from app.ai_interview.answer_engine.answer_evaluator import FakeAnswerEvaluator
from app.ai_interview.answer_engine.schemas import AnswerSubmission
from app.ai_interview.orchestration.interview_turn_coordinator import InterviewTurnCoordinator

@pytest.fixture
def coordinator():
    q_engine = QuestionEngine(
        generator=FakeQuestionGenerator()
    )
    a_engine = AnswerEngine(evaluator=FakeAnswerEvaluator())
    return InterviewTurnCoordinator(question_engine=q_engine, answer_engine=a_engine)

@pytest.fixture
def initial_session():
    topic1 = TopicBlueprint(topic_id="t1", topic_name="Python Basics", source="Resume", priority=1, mandatory=True, initial_difficulty=DifficultyLevel.EASY, allowed_question_types=[], question_budget=3)
    topic2 = TopicBlueprint(topic_id="t2", topic_name="Advanced Async", source="Resume", priority=0, mandatory=True, initial_difficulty=DifficultyLevel.MEDIUM, allowed_question_types=[], question_budget=2)
    bp = InterviewBlueprint(blueprint_version="1", total_question_budget=10, min_questions=2, max_questions=10, emergency_max_questions=15, topics=[topic1, topic2])
    
    session = InterviewSessionSchema(
        session_id="s1", candidate_id="c1", company_id="comp1", campaign_id="camp1", mode_id="m1", mode_version=1,
        state=InterviewState.CREATED, blueprint=bp, created_at=datetime.utcnow()
    )
    
    session.topic_progress = [
        TopicProgress(topic_id="t1", state=TopicState.NOT_STARTED),
        TopicProgress(topic_id="t2", state=TopicState.NOT_STARTED)
    ]
    return session

@pytest.fixture
def mock_mode():
    return InterviewModeDefinition(
        mode_id="m1", name="Technical", description="", version=1, status="published",
        settings=InterviewModeSettings(allowed_question_types=["initial"], difficulty_policy="medium"),
        created_at=datetime.utcnow()
    )

from app.ai_interview.resume_processing.schemas import ExtractionMetadata
from app.ai_interview.resume_processing.enums import ExtractionQualityStatus
from app.ai_interview.schemas.resume import StructuredResume

@pytest.fixture
def mock_context():
    return CandidateInterviewContext(
        candidate_id="c1",
        structured_resume=StructuredResume(),
        extraction_metadata=ExtractionMetadata(source_type="pdf", extractor_name="t", extractor_version="1", character_count=1, detected_sections=[], warning_count=0, processing_duration_ms=0.0),
        quality_status=ExtractionQualityStatus.USABLE
    )

def test_full_multi_turn_flow(coordinator, initial_session, mock_mode, mock_context):
    session = initial_session
    
    # TURN 1: Start interview
    res = coordinator.advance_interview(session, mock_context, mock_mode)
    assert res.action == RuntimeAction.NO_ACTION
    assert res.waiting_for_answer is True
    assert res.question is not None
    assert res.current_topic_id == "t1"
    
    # TURN 2: Answer weak (not enough to cover topic t1, budget is 3)
    sub = AnswerSubmission(session_id="s1", question_record_id=res.question.record_id, answer_text="weak answer")
    res = coordinator.advance_interview(session, mock_context, mock_mode, answer_submission=sub)
    
    assert res.action == RuntimeAction.NO_ACTION
    assert res.waiting_for_answer is True
    assert res.question is not None # Follow-up or next question in t1
    assert res.current_topic_id == "t1"
    assert len(session.evaluation_history) == 1
    assert session.topic_progress[0].state == TopicState.IN_PROGRESS
    
    # TURN 3: Answer excellent
    sub = AnswerSubmission(session_id="s1", question_record_id=res.question.record_id, answer_text="excellent answer")
    res = coordinator.advance_interview(session, mock_context, mock_mode, answer_submission=sub)
    
    # Budget is 3, 2 questions asked. Need to see if it advances. Not advanced.
    assert res.current_topic_id == "t1"
    
    # TURN 4: Answer excellent again
    sub = AnswerSubmission(session_id="s1", question_record_id=res.question.record_id, answer_text="excellent answer")
    res = coordinator.advance_interview(session, mock_context, mock_mode, answer_submission=sub)
    
    # Now topic t1 has 3 questions. Budget is hit. Average is good (weak + 2 excellent).
    # So t1 will be covered, and we advance to t2.
    assert session.topic_progress[0].state == TopicState.COVERED
    assert res.current_topic_id == "t2"
    
    # TURN 5: Answer excellent for t2 (budget is 2)
    sub = AnswerSubmission(session_id="s1", question_record_id=res.question.record_id, answer_text="excellent answer")
    res = coordinator.advance_interview(session, mock_context, mock_mode, answer_submission=sub)
    assert res.current_topic_id == "t2"
    
    # TURN 6: Answer excellent for t2
    sub = AnswerSubmission(session_id="s1", question_record_id=res.question.record_id, answer_text="excellent answer")
    res = coordinator.advance_interview(session, mock_context, mock_mode, answer_submission=sub)
    
    # t2 budget hit, both covered. Interview should complete!
    assert res.interview_completed is True
    assert res.action == RuntimeAction.COMPLETE
    assert session.state == InterviewState.COMPLETED
