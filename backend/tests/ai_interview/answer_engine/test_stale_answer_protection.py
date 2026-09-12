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
        questions_asked_total=2
    )
    session.topic_progress = [TopicProgress(topic_id="t1", state=TopicState.IN_PROGRESS, questions_asked=2)]
    session.current_topic_id = "t1"
    
    # Q1 was generated and answered
    session.question_history.append(
        QuestionRecord(record_id="q1", session_id="s1", turn_number=1, topic_id="t1", question_text="What is X?", question_type=QuestionType.INITIAL, difficulty=DifficultyLevel.EASY)
    )
    # Q2 was generated and is waiting for answer
    session.question_history.append(
        QuestionRecord(record_id="q2", session_id="s1", turn_number=2, topic_id="t1", question_text="What is Y?", question_type=QuestionType.FOLLOW_UP, difficulty=DifficultyLevel.MEDIUM)
    )
    
    # Q1 was evaluated
    from app.ai_interview.answer_engine.schemas import EvaluationRecord
    from app.ai_interview.answer_engine.enums import CoverageSignal, FollowUpSignal
    session.evaluation_history.append(
        EvaluationRecord(evaluation_id="e1", question_record_id="q1", topic_id="t1", overall_score=0.5, qualitative_coverage_signal=CoverageSignal.PARTIALLY_COVERED, follow_up_signal=FollowUpSignal.NONE)
    )
    
    return session

@pytest.fixture
def mock_mode():
    return InterviewModeDefinition(
        mode_id="m1", name="Technical", description="", version=1, status="published",
        settings=InterviewModeSettings(allowed_question_types=["initial"], difficulty_policy="medium"),
        created_at=datetime.utcnow()
    )

def test_answer_for_wrong_session_rejected(engine, mock_session, mock_mode):
    # Answer targets q2 but from a different session ID
    sub = AnswerSubmission(session_id="WRONG_SESSION", question_record_id="q2", answer_text="Valid answer text")
    
    with pytest.raises(QuestionCorrelationError, match="not s1"):
        engine.evaluate_answer(sub, mock_session, mock_mode)

def test_answer_for_nonexistent_question_rejected(engine, mock_session, mock_mode):
    sub = AnswerSubmission(session_id="s1", question_record_id="q999_fake", answer_text="Valid answer text")
    
    with pytest.raises(QuestionCorrelationError, match="not found"):
        engine.evaluate_answer(sub, mock_session, mock_mode)

def test_stale_answer_for_already_evaluated_question_rejected(engine, mock_session, mock_mode):
    # Candidate somehow submits late answer for Q1
    sub = AnswerSubmission(session_id="s1", question_record_id="q1", answer_text="Valid late answer text")
    
    # Must be rejected because Q1 is already evaluated
    with pytest.raises(QuestionCorrelationError, match="already been evaluated"):
        engine.evaluate_answer(sub, mock_session, mock_mode)
