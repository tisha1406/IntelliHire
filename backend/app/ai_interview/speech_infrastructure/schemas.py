from typing import Optional
from pydantic import BaseModel

class TranscriptionResult(BaseModel):
    """
    STT Data Contract.
    Minimal metadata. We do NOT expose raw provider responses.
    """
    transcript: str
    language: Optional[str] = None
    duration_ms: int
    provider: str

class SpeechSynthesisResult(BaseModel):
    """
    TTS Data Contract.
    Contains the binary audio and mime type.
    """
    audio_bytes: bytes
    mime_type: str
    provider: str
    duration_ms: Optional[int] = None
