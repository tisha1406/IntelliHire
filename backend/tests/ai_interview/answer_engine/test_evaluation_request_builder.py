import pytest
from app.ai_interview.answer_engine.evaluation_request_builder import EvaluationRequestBuilder
from app.ai_interview.answer_engine.schemas import AnswerSubmission, ProcessedAnswer, EvaluationRecord
from app.ai_interview.schemas.session import InterviewSessionSchema
from app.ai_interview.schemas.interview_mode import InterviewModeDefinition, InterviewModeSettings
from app.ai_interview.question_engine.schemas import QuestionRecord
from app.ai_interview.core.enums import InterviewState, QuestionType, DifficultyLevel
from app.ai_interview.schemas.blueprint import InterviewBlueprint
from datetime import datetime
from app.ai_interview.answer_engine.enums import AnswerValidity, CoverageSignal, FollowUpSignal
from app.ai_interview.answer_engine.exceptions import QuestionCorrelationError

@pytest.fixture
def mock_session():
    bp = InterviewBlueprint(blueprint_version="1", total_question_budget=5, min_questions=1, max_questions=5, emergency_max_questions=7, topics=[])
    session = InterviewSessionSchema(
        session_id="s1",
        candidate_id="c1",
        company_id="comp1",
        campaign_id="camp1",
        mode_id="m1",
        mode_version=1,
        state=InterviewState.IN_PROGRESS,
        blueprint=bp,
        created_at=datetime.utcnow()
    )
    # Add a mock question record
    qr = QuestionRecord(
        record_id="q1",
        session_id="s1",
        turn_number=1,
        topic_id="t1",
        question_text="What is Python?",
        question_type=QuestionType.INITIAL,
        difficulty=DifficultyLevel.EASY
    )
    session.question_history.append(qr)
    return session

@pytest.fixture
def mock_mode():
    return InterviewModeDefinition(
        mode_id="m1",
        name="Technical",
        description="",
        version=1,
        status="published",
        settings=InterviewModeSettings(allowed_question_types=["initial"], difficulty_policy="medium"),
        created_at=datetime.utcnow()
    )

def test_builder_successful(mock_session, mock_mode):
    sub = AnswerSubmission(session_id="s1", question_record_id="q1", answer_text="A language")
    proc = ProcessedAnswer(original_text="A language", normalized_text="A language", word_count=2, character_count=10, validity=AnswerValidity.VALID)
    
    req = EvaluationRequestBuilder.build(sub, proc, mock_session, mock_mode)
    
    assert req.question_record_id == "q1"
    assert req.candidate_answer == "A language"
    assert "Technical" in req.interview_mode_criteria["focus_areas"]

def test_builder_wrong_session(mock_session, mock_mode):
    sub = AnswerSubmission(session_id="s2", question_record_id="q1", answer_text="A language")
    proc = ProcessedAnswer(original_text="A language", normalized_text="A language", word_count=2, character_count=10, validity=AnswerValidity.VALID)
    
    with pytest.raises(QuestionCorrelationError, match="not s1"):
        EvaluationRequestBuilder.build(sub, proc, mock_session, mock_mode)

def test_builder_question_not_found(mock_session, mock_mode):
    sub = AnswerSubmission(session_id="s1", question_record_id="q2", answer_text="A language")
    proc = ProcessedAnswer(original_text="A language", normalized_text="A language", word_count=2, character_count=10, validity=AnswerValidity.VALID)
    
    with pytest.raises(QuestionCorrelationError, match="not found"):
        EvaluationRequestBuilder.build(sub, proc, mock_session, mock_mode)

def test_builder_idempotency_duplicate_evaluation(mock_session, mock_mode):
    # Simulate already evaluated
    er = EvaluationRecord(evaluation_id="e1", question_record_id="q1", topic_id="t1", overall_score=1.0, qualitative_coverage_signal=CoverageSignal.NOT_COVERED, follow_up_signal=FollowUpSignal.NONE)
    mock_session.evaluation_history.append(er)
    
    sub = AnswerSubmission(session_id="s1", question_record_id="q1", answer_text="A language")
    proc = ProcessedAnswer(original_text="A language", normalized_text="A language", word_count=2, character_count=10, validity=AnswerValidity.VALID)
    
    with pytest.raises(QuestionCorrelationError, match="already been evaluated"):
        EvaluationRequestBuilder.build(sub, proc, mock_session, mock_mode)
