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
from app.ai_interview.answer_engine.exceptions import AnswerEvaluationError

@pytest.fixture
def failing_engine():
    # Evaluator that fails every generation attempt to simulate API crash
    return AnswerEngine(evaluator=FakeAnswerEvaluator(fail_mode=True, malformed_mode=True))

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

def test_evaluation_exhaustion_leaves_session_unmutated(failing_engine, mock_session, mock_mode):
    sub = AnswerSubmission(session_id="s1", question_record_id="q1", answer_text="Valid answer text")
    
    with pytest.raises(AnswerEvaluationError, match="after 3 attempts"):
        failing_engine.evaluate_answer(sub, mock_session, mock_mode)
        
    # INVARIANTS:
    # No evaluation history appended
    assert len(mock_session.evaluation_history) == 0
    # No question history mutated or deleted
    assert len(mock_session.question_history) == 1
    # questions_asked_total remains the same
    assert mock_session.questions_asked_total == 1
    # topic.questions_asked remains the same
    assert mock_session.topic_progress[0].questions_asked == 1
    # Evaluation aggregates are completely untouched
    assert mock_session.topic_progress[0].evaluation_aggregate.answers_evaluated == 0
    # Topic state is untouched
    assert mock_session.topic_progress[0].state == TopicState.IN_PROGRESS
    assert mock_session.topic_progress[0].qualitatively_covered is False
    # Interview state is untouched
    assert mock_session.state == InterviewState.IN_PROGRESS
