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
from app.ai_interview.answer_engine.schemas import AnswerSubmission

@pytest.fixture
def coordinator():
    q = QuestionEngine(generator=FakeQuestionGenerator())
    a = AnswerEngine(evaluator=FakeAnswerEvaluator())
    return InterviewTurnCoordinator(question_engine=q, answer_engine=a)

@pytest.fixture
def session_with_low_budget():
    t1 = TopicBlueprint(topic_id="t1", topic_name="T1", source="Resume", priority=1, mandatory=True, initial_difficulty=DifficultyLevel.EASY, allowed_question_types=[], question_budget=1)
    bp = InterviewBlueprint(blueprint_version="1", total_question_budget=5, min_questions=1, max_questions=5, emergency_max_questions=7, topics=[t1])
    
    session = InterviewSessionSchema(
        session_id="s1", candidate_id="c1", company_id="comp1", campaign_id="camp1", mode_id="m1", mode_version=1,
        state=InterviewState.CREATED, blueprint=bp, created_at=datetime.utcnow()
    )
    session.topic_progress = [TopicProgress(topic_id="t1", state=TopicState.NOT_STARTED)]
    return session

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

def test_budget_protection_exhaustion_moves_to_next(coordinator, session_with_low_budget, context, mode):
    # t1 has budget of exactly 1
    res = coordinator.advance_interview(session_with_low_budget, context, mode)
    assert res.current_topic_id == "t1"
    
    # 1st answer - but very weak
    sub = AnswerSubmission(session_id="s1", question_record_id=res.question.record_id, answer_text="weak answer")
    res = coordinator.advance_interview(session_with_low_budget, context, mode, answer_submission=sub)
    
    # Topic budget was 1. The answer was weak. 
    # Because budget is exhausted and avg < 0.5, it becomes FAILED_ABANDONED.
    assert session_with_low_budget.topic_progress[0].state == TopicState.FAILED_ABANDONED
    
    # Since it was the only topic, interview completes immediately.
    assert res.interview_completed is True
