import re
from app.ai_interview.answer_engine.schemas import AnswerSubmission, ProcessedAnswer
from app.ai_interview.answer_engine.enums import AnswerValidity
from app.ai_interview.answer_engine.config import MIN_ANSWER_LENGTH, MAX_ANSWER_LENGTH
from app.ai_interview.answer_engine.exceptions import AnswerValidationError

class AnswerProcessor:
    """
    Deterministically processes and validates the raw answer.
    Does not perform semantic analysis.
    """
    
    @staticmethod
    def process(submission: AnswerSubmission) -> ProcessedAnswer:
        original = submission.answer_text
        if original is None:
            raise AnswerValidationError("Answer cannot be completely empty or null.")
            
        # Strip leading/trailing and normalize repeated whitespaces safely
        normalized = original.strip()
        normalized = re.sub(r'\s+', ' ', normalized)
        
        char_count = len(normalized)
        word_count = len(normalized.split()) if normalized else 0
        
        if char_count == 0:
            validity = AnswerValidity.EMPTY
        elif char_count < MIN_ANSWER_LENGTH:
            validity = AnswerValidity.TOO_SHORT
        elif char_count > MAX_ANSWER_LENGTH:
            validity = AnswerValidity.INVALID
        else:
            validity = AnswerValidity.VALID
            
        if validity != AnswerValidity.VALID:
            raise AnswerValidationError(f"Answer is invalid: {validity.value}")
            
        return ProcessedAnswer(
            original_text=original,
            normalized_text=normalized,
            word_count=word_count,
            character_count=char_count,
            validity=validity
        )
