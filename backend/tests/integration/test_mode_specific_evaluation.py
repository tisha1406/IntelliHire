import pytest
from datetime import datetime
from app.ai_interview.answer_engine.answer_engine import AnswerEngine
from app.ai_interview.answer_engine.answer_evaluator import FakeAnswerEvaluator
from app.ai_interview.answer_engine.schemas import AnswerSubmission, ProcessedAnswer
from app.ai_interview.schemas.session import InterviewSessionSchema, TopicProgress
from app.ai_interview.schemas.blueprint import InterviewBlueprint, TopicBlueprint
from app.ai_interview.schemas.interview_mode import InterviewModeDefinition, InterviewModeSettings
from app.ai_interview.core.enums import InterviewState, TopicState, QuestionType, DifficultyLevel
from app.ai_interview.question_engine.schemas import QuestionRecord
from app.ai_interview.answer_engine.evaluation_request_builder import EvaluationRequestBuilder

@pytest.fixture
def mock_session():
    topic_bp = TopicBlueprint(topic_id="t1", topic_name="T1", source="s", priority=1, mandatory=True, initial_difficulty=DifficultyLevel.EASY, allowed_question_types=[], question_budget=2)
    bp = InterviewBlueprint(blueprint_version="1", total_question_budget=5, min_questions=1, max_questions=5, emergency_max_questions=7, topics=[topic_bp])
    session = InterviewSessionSchema(
        session_id="s1", candidate_id="c1", company_id="comp1", campaign_id="camp1", mode_id="m1", mode_version=1,
        state=InterviewState.IN_PROGRESS, blueprint=bp, created_at=datetime.utcnow()
    )
    prog = TopicProgress(topic_id="t1", state=TopicState.IN_PROGRESS)
    session.topic_progress.append(prog)
    qr = QuestionRecord(record_id="q1", session_id="s1", turn_number=1, topic_id="t1", question_text="Q", question_type=QuestionType.INITIAL, difficulty=DifficultyLevel.EASY)
    session.question_history.append(qr)
    return session

def test_technical_mode_criteria(mock_session):
    mode = InterviewModeDefinition(
        mode_id="m1", name="Technical Interview", description="", version=1, status="published",
        settings=InterviewModeSettings(allowed_question_types=["initial"], difficulty_policy="medium"),
        created_at=datetime.utcnow()
    )
    sub = AnswerSubmission(session_id="s1", question_record_id="q1", answer_text="excellent answer")
    proc = ProcessedAnswer(original_text="A", normalized_text="A", word_count=2, character_count=10, validity="valid")
    
    req = EvaluationRequestBuilder.build(sub, proc, mock_session, mode)
    assert "Technical correctness" in req.interview_mode_criteria["focus_areas"]

def test_behavioral_mode_criteria(mock_session):
    mode = InterviewModeDefinition(
        mode_id="m1", name="Behavioral Interview", description="", version=1, status="published",
        settings=InterviewModeSettings(allowed_question_types=["initial"], difficulty_policy="medium"),
        created_at=datetime.utcnow()
    )
    sub = AnswerSubmission(session_id="s1", question_record_id="q1", answer_text="excellent answer")
    proc = ProcessedAnswer(original_text="A", normalized_text="A", word_count=2, character_count=10, validity="valid")
    
    req = EvaluationRequestBuilder.build(sub, proc, mock_session, mode)
    assert "STAR structure" in req.interview_mode_criteria["focus_areas"]
