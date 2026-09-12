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
from app.ai_interview.core.enums import InterviewState, TopicState, DifficultyLevel, QuestionType
from app.ai_interview.runtime.enums import RuntimeAction
from app.ai_interview.answer_engine.schemas import AnswerSubmission
from app.ai_interview.question_engine.schemas import QuestionRecord
from app.ai_interview.answer_engine.exceptions import QuestionCorrelationError

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

@pytest.mark.parametrize("terminal_state", [
    InterviewState.COMPLETED,
    InterviewState.FAILED,
])
def test_terminal_state_prevents_question_generation(coordinator, context, mode, terminal_state):
    t1 = TopicBlueprint(topic_id="t1", topic_name="T1", source="Resume", priority=1, mandatory=True, initial_difficulty=DifficultyLevel.EASY, allowed_question_types=[], question_budget=3)
    bp = InterviewBlueprint(blueprint_version="1", total_question_budget=5, min_questions=1, max_questions=5, emergency_max_questions=7, topics=[t1])
    
    session = InterviewSessionSchema(
        session_id="s1", candidate_id="c1", company_id="comp1", campaign_id="camp1", mode_id="m1", mode_version=1,
        state=terminal_state, blueprint=bp, created_at=datetime.utcnow()
    )
    
    res = coordinator.advance_interview(session, context, mode)
    assert res.action == RuntimeAction.NO_ACTION
    assert res.question is None
    assert session.questions_asked_total == 0

@pytest.mark.parametrize("terminal_state", [
    InterviewState.COMPLETED,
    InterviewState.FAILED,
])
def test_terminal_state_prevents_answer_evaluation(coordinator, context, mode, terminal_state):
    t1 = TopicBlueprint(topic_id="t1", topic_name="T1", source="Resume", priority=1, mandatory=True, initial_difficulty=DifficultyLevel.EASY, allowed_question_types=[], question_budget=3)
    bp = InterviewBlueprint(blueprint_version="1", total_question_budget=5, min_questions=1, max_questions=5, emergency_max_questions=7, topics=[t1])
    
    session = InterviewSessionSchema(
        session_id="s1", candidate_id="c1", company_id="comp1", campaign_id="camp1", mode_id="m1", mode_version=1,
        state=terminal_state, blueprint=bp, created_at=datetime.utcnow()
    )
    
    # Q1 was dispatched before the session became terminal
    session.question_history.append(
        QuestionRecord(record_id="q1", session_id="s1", turn_number=1, topic_id="t1", question_text="What is X?", question_type=QuestionType.INITIAL, difficulty=DifficultyLevel.EASY)
    )
    
    sub = AnswerSubmission(session_id="s1", question_record_id="q1", answer_text="Valid answer text")
    
    from app.ai_interview.answer_engine.exceptions import AnswerEvaluationError
    
    with pytest.raises(AnswerEvaluationError, match="terminal"):
        coordinator.advance_interview(session, context, mode, answer_submission=sub)
    
    # Invariant: session evaluation history remains 0
    assert len(session.evaluation_history) == 0
