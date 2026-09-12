import pytest
from datetime import datetime
from app.ai_interview.orchestration.interview_turn_coordinator import InterviewTurnCoordinator
from app.ai_interview.answer_engine.answer_engine import AnswerEngine
from app.ai_interview.answer_engine.answer_evaluator import FakeAnswerEvaluator
from app.ai_interview.question_engine.question_engine import QuestionEngine
from app.ai_interview.question_engine.question_generator import FakeQuestionGenerator
from app.ai_interview.schemas.session import InterviewSessionSchema, TopicProgress
from app.ai_interview.schemas.blueprint import InterviewBlueprint, TopicBlueprint
from app.ai_interview.schemas.interview_mode import InterviewModeDefinition, InterviewModeSettings
from app.ai_interview.resume_processing.schemas import CandidateInterviewContext, ExtractionMetadata
from app.ai_interview.resume_processing.enums import ExtractionQualityStatus
from app.ai_interview.schemas.resume import StructuredResume
from app.ai_interview.core.enums import InterviewState, TopicState, DifficultyLevel
from app.ai_interview.runtime.enums import RuntimeAction
from app.ai_interview.runtime.schemas import RuntimeDecision

@pytest.fixture
def coordinator():
    q = QuestionEngine(generator=FakeQuestionGenerator())
    a = AnswerEngine(evaluator=FakeAnswerEvaluator())
    return InterviewTurnCoordinator(question_engine=q, answer_engine=a)

@pytest.fixture
def context():
    return CandidateInterviewContext(
        candidate_id="c1",
        structured_resume=StructuredResume(),
        extraction_metadata=ExtractionMetadata(source_type="pdf", extractor_name="t", extractor_version="1", character_count=1, detected_sections=[], warning_count=0, processing_duration_ms=0.0),
        quality_status=ExtractionQualityStatus.USABLE
    )

@pytest.fixture
def mode():
    return InterviewModeDefinition(
        mode_id="m1", name="Technical", description="", version=1, status="published",
        settings=InterviewModeSettings(allowed_question_types=["initial"], difficulty_policy="medium"),
        created_at=datetime.utcnow()
    )

def test_coordinator_cannot_bypass_runtime_denial(coordinator, context, mode):
    # Setup session in a paused state, which runtime should deny questions for
    t1 = TopicBlueprint(topic_id="t1", topic_name="T1", source="Resume", priority=1, mandatory=True, initial_difficulty=DifficultyLevel.EASY, allowed_question_types=[], question_budget=3)
    bp = InterviewBlueprint(blueprint_version="1", total_question_budget=5, min_questions=1, max_questions=5, emergency_max_questions=7, topics=[t1])
    
    session = InterviewSessionSchema(
        session_id="s1", candidate_id="c1", company_id="comp1", campaign_id="camp1", mode_id="m1", mode_version=1,
        state=InterviewState.PAUSED, blueprint=bp, created_at=datetime.utcnow()
    )
    session.topic_progress = [TopicProgress(topic_id="t1", state=TopicState.NOT_STARTED)]
    
    res = coordinator.advance_interview(session, context, mode)
    
    # Assert the coordinator does not generate a question and passes through RESUME
    assert res.action == RuntimeAction.RESUME
    assert res.waiting_for_answer is False
    assert res.question is None
    # Ensure no mutation bypassed
    assert session.state == InterviewState.PAUSED
    assert session.questions_asked_total == 0

def test_coordinator_cannot_manually_complete_interview(coordinator, context, mode):
    # Setup session with pending topics
    t1 = TopicBlueprint(topic_id="t1", topic_name="T1", source="Resume", priority=1, mandatory=True, initial_difficulty=DifficultyLevel.EASY, allowed_question_types=[], question_budget=3)
    bp = InterviewBlueprint(blueprint_version="1", total_question_budget=5, min_questions=1, max_questions=5, emergency_max_questions=7, topics=[t1])
    
    session = InterviewSessionSchema(
        session_id="s1", candidate_id="c1", company_id="comp1", campaign_id="camp1", mode_id="m1", mode_version=1,
        state=InterviewState.CREATED, blueprint=bp, created_at=datetime.utcnow()
    )
    session.topic_progress = [TopicProgress(topic_id="t1", state=TopicState.NOT_STARTED)]
    
    # Try to trick coordinator - not really possible since we only call advance_interview
    # But we assert that advance_interview correctly starts the topic and asks a question, not completes it
    res = coordinator.advance_interview(session, context, mode)
    assert res.interview_completed is False
    assert session.state == InterviewState.IN_PROGRESS
    assert session.current_topic_id == "t1"
