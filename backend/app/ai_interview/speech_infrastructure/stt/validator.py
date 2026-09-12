from app.ai_interview.speech_infrastructure.schemas import TranscriptionResult
from app.ai_interview.speech_infrastructure.exceptions import STTValidationError

class STTValidator:
    """
    Validates the TranscriptionResult returned by the SpeechToTextProvider.
    Ensures that empty or malformed transcripts are rejected before reaching the candidate preview.
    """
    MAX_TRANSCRIPT_LENGTH = 10000

    @classmethod
    def validate(cls, result: TranscriptionResult) -> None:
        transcript = result.transcript.strip()
        if not transcript:
            raise STTValidationError("Transcript is empty or whitespace-only.")
        
        if len(transcript) > cls.MAX_TRANSCRIPT_LENGTH:
            raise STTValidationError(f"Transcript exceeds maximum length of {cls.MAX_TRANSCRIPT_LENGTH} characters.")
        
        if result.duration_ms <= 0:
            raise STTValidationError("Invalid audio duration returned by provider.")
