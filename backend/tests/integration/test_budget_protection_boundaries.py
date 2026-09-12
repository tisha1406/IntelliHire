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

def test_budget_boundary(coordinator, context, mode):
    # Setup session with strict budget of 2
    t1 = TopicBlueprint(topic_id="t1", topic_name="T1", source="Resume", priority=1, mandatory=True, initial_difficulty=DifficultyLevel.EASY, allowed_question_types=[], question_budget=2)
    bp = InterviewBlueprint(blueprint_version="1", total_question_budget=5, min_questions=1, max_questions=5, emergency_max_questions=7, topics=[t1])
    
    session = InterviewSessionSchema(
        session_id="s1", candidate_id="c1", company_id="comp1", campaign_id="camp1", mode_id="m1", mode_version=1,
        state=InterviewState.CREATED, blueprint=bp, created_at=datetime.utcnow()
    )
    session.topic_progress = [TopicProgress(topic_id="t1", state=TopicState.NOT_STARTED)]
    
    # 1. First question
    res1 = coordinator.advance_interview(session, context, mode)
    assert res1.question is not None
    assert session.topic_progress[0].questions_asked == 1
    
    # Answer 1 (weak to trigger a follow up instead of early coverage)
    sub1 = AnswerSubmission(session_id="s1", question_record_id=res1.question.record_id, answer_text="weak answer")
    res2 = coordinator.advance_interview(session, context, mode, answer_submission=sub1)
    
    # 2. Second question (Follow up)
    assert res2.question is not None
    assert session.topic_progress[0].questions_asked == 2
    
    # Answer 2 (weak again)
    sub2 = AnswerSubmission(session_id="s1", question_record_id=res2.question.record_id, answer_text="weak answer")
    res3 = coordinator.advance_interview(session, context, mode, answer_submission=sub2)
    
    # Budget exhausted. 
    # Because there are no more topics and budget is hit, the interview will complete 
    # and NO third question will be generated.
    assert res3.question is None
    assert session.topic_progress[0].questions_asked == 2
    assert session.questions_asked_total == 2
    assert res3.interview_completed is True
