import pytest
from app.ai_interview.answer_engine.answer_processor import AnswerProcessor
from app.ai_interview.answer_engine.schemas import AnswerSubmission
from app.ai_interview.answer_engine.enums import AnswerValidity
from app.ai_interview.answer_engine.exceptions import AnswerValidationError

def test_answer_processor_valid():
    sub = AnswerSubmission(session_id="s1", question_record_id="q1", answer_text="This is a valid answer.")
    res = AnswerProcessor.process(sub)
    assert res.validity == AnswerValidity.VALID
    assert res.word_count == 5
    assert res.original_text == "This is a valid answer."
    
def test_answer_processor_whitespace_normalization():
    sub = AnswerSubmission(session_id="s1", question_record_id="q1", answer_text="   This   is   spaced   ")
    res = AnswerProcessor.process(sub)
    assert res.normalized_text == "This is spaced"
    assert res.validity == AnswerValidity.VALID
    
def test_answer_processor_empty():
    sub = AnswerSubmission(session_id="s1", question_record_id="q1", answer_text="   ")
    with pytest.raises(AnswerValidationError):
        AnswerProcessor.process(sub)
        
def test_answer_processor_too_short():
    sub = AnswerSubmission(session_id="s1", question_record_id="q1", answer_text="no")
    with pytest.raises(AnswerValidationError):
        AnswerProcessor.process(sub)
