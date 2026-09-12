import pytest
from app.ai_interview.speech_infrastructure.schemas import TranscriptionResult
from app.ai_interview.speech_infrastructure.stt.validator import STTValidator
from app.ai_interview.speech_infrastructure.exceptions import STTValidationError

def test_empty_transcript():
    result = TranscriptionResult(transcript="", duration_ms=1000, provider="mock")
    with pytest.raises(STTValidationError, match="empty or whitespace-only"):
        STTValidator.validate(result)

def test_whitespace_transcript():
    result = TranscriptionResult(transcript="   \n  \t ", duration_ms=1000, provider="mock")
    with pytest.raises(STTValidationError, match="empty or whitespace-only"):
        STTValidator.validate(result)

def test_oversized_transcript():
    result = TranscriptionResult(transcript="a" * 10001, duration_ms=1000, provider="mock")
    with pytest.raises(STTValidationError, match="exceeds maximum length"):
        STTValidator.validate(result)

def test_invalid_duration():
    result = TranscriptionResult(transcript="Valid answer", duration_ms=0, provider="mock")
    with pytest.raises(STTValidationError, match="Invalid audio duration"):
        STTValidator.validate(result)

def test_valid_transcript():
    result = TranscriptionResult(transcript="This is a valid answer.", duration_ms=5000, provider="mock")
    STTValidator.validate(result)  # Should not raise
