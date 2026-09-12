import pytest
from datetime import datetime
from app.ai_interview.answer_engine.answer_engine import AnswerEngine
from app.ai_interview.answer_engine.answer_evaluator import FakeAnswerEvaluator
from app.ai_interview.answer_engine.schemas import AnswerSubmission
from app.ai_interview.schemas.session import InterviewSessionSchema, TopicProgress
from app.ai_interview.schemas.blueprint import InterviewBlueprint, TopicBlueprint
from app.ai_interview.schemas.interview_mode import InterviewModeDefinition, InterviewModeSettings
from app.ai_interview.core.enums import InterviewState, TopicState, DifficultyLevel, QuestionType
from app.ai_interview.question_engine.schemas import QuestionRecord
from app.ai_interview.answer_engine.exceptions import QuestionCorrelationError

@pytest.fixture
def engine():
    return AnswerEngine(evaluator=FakeAnswerEvaluator())

@pytest.fixture
def mock_session():
    t1 = TopicBlueprint(topic_id="t1", topic_name="T1", source="Resume", priority=1, mandatory=True, initial_difficulty=DifficultyLevel.EASY, allowed_question_types=[], question_budget=3)
    bp = InterviewBlueprint(blueprint_version="1", total_question_budget=5, min_questions=1, max_questions=5, emergency_max_questions=7, topics=[t1])
    
    session = InterviewSessionSchema(
        session_id="s1", candidate_id="c1", company_id="comp1", campaign_id="camp1", mode_id="m1", mode_version=1,
        state=InterviewState.IN_PROGRESS, blueprint=bp, created_at=datetime.utcnow(),
        questions_asked_total=1
    )
    session.topic_progress = [TopicProgress(topic_id="t1", state=TopicState.IN_PROGRESS, questions_asked=1)]
    session.current_topic_id = "t1"
    session.question_history.append(
        QuestionRecord(record_id="q1", session_id="s1", turn_number=1, topic_id="t1", question_text="What is X?", question_type=QuestionType.INITIAL, difficulty=DifficultyLevel.EASY)
    )
    return session

@pytest.fixture
def mock_mode():
    return InterviewModeDefinition(
        mode_id="m1", name="Technical", description="", version=1, status="published",
        settings=InterviewModeSettings(allowed_question_types=["initial"], difficulty_policy="medium"),
        created_at=datetime.utcnow()
    )

def test_duplicate_evaluation_is_rejected(engine, mock_session, mock_mode):
    sub = AnswerSubmission(session_id="s1", question_record_id="q1", answer_text="Valid answer text")
    
    # First evaluation succeeds
    res1 = engine.evaluate_answer(sub, mock_session, mock_mode)
    assert len(mock_session.evaluation_history) == 1
    
    # Second evaluation of the same question record
    with pytest.raises(QuestionCorrelationError, match="already been evaluated"):
        engine.evaluate_answer(sub, mock_session, mock_mode)
        
    # Ensure no duplicate mutation occurred
    assert len(mock_session.evaluation_history) == 1
    assert mock_session.topic_progress[0].evaluation_aggregate.answers_evaluated == 1

def test_different_answer_for_same_question_is_rejected(engine, mock_session, mock_mode):
    sub1 = AnswerSubmission(session_id="s1", question_record_id="q1", answer_text="Valid answer text")
    sub2 = AnswerSubmission(session_id="s1", question_record_id="q1", answer_text="A completely different but valid answer text")
    
    # First evaluation succeeds
    engine.evaluate_answer(sub1, mock_session, mock_mode)
    
    # Second evaluation of the SAME question record with DIFFERENT text
    with pytest.raises(QuestionCorrelationError, match="already been evaluated"):
        engine.evaluate_answer(sub2, mock_session, mock_mode)
        
    # Ensure no revision was accepted. The invariant is: 1 QuestionRecord = max 1 EvaluationRecord
    assert len(mock_session.evaluation_history) == 1
