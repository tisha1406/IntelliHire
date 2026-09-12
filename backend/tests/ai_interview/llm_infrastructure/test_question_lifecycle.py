import pytest
from app.ai_interview.question_engine.enums import QuestionStatus
from app.ai_interview.question_engine.schemas import QuestionRecord
from app.ai_interview.core.enums import DifficultyLevel, QuestionType

def test_question_status_lifecycle():
    record = QuestionRecord(
        session_id="s1",
        turn_number=1,
        topic_id="t1",
        question_text="What is Python?",
        question_type=QuestionType.INITIAL,
        difficulty=DifficultyLevel.EASY
    )
    
    assert record.status == QuestionStatus.DISPATCHED
    
    # Valid transitions
    record.status = QuestionStatus.ANSWER_RECEIVED
    assert record.status == QuestionStatus.ANSWER_RECEIVED
    
    record.status = QuestionStatus.EVALUATION_PENDING
    assert record.status == QuestionStatus.EVALUATION_PENDING
    
    record.status = QuestionStatus.EVALUATED
    assert record.status == QuestionStatus.EVALUATED

def test_question_status_enum_values():
    assert QuestionStatus.GENERATED.value == "generated"
    assert QuestionStatus.DISPATCHED.value == "dispatched"
    assert QuestionStatus.ANSWER_RECEIVED.value == "answer_received"
    assert QuestionStatus.EVALUATION_PENDING.value == "evaluation_pending"
    assert QuestionStatus.EVALUATED.value == "evaluated"
