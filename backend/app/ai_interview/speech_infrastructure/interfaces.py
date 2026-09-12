from typing import Protocol, runtime_checkable, Optional
from app.ai_interview.speech_infrastructure.schemas import TranscriptionResult, SpeechSynthesisResult

@runtime_checkable
class SpeechToTextProvider(Protocol):
    """
    Abstract Speech-to-Text provider interface.
    The deterministic engine and endpoints must never know which concrete provider is used.
    """
    
    async def transcribe(self, audio_bytes: bytes, mime_type: str) -> TranscriptionResult:
        """
        Transcribe raw audio bytes into text.
        
        Args:
            audio_bytes: The raw audio file contents.
            mime_type: The content type of the audio.
            
        Returns:
            TranscriptionResult containing transcript and metadata.
            
        Raises:
            STTProviderError: Base class for STT errors.
        """
        ...

@runtime_checkable
class TextToSpeechProvider(Protocol):
    """
    Abstract Text-to-Speech provider interface.
    """
    
    async def synthesize(self, text: str, language: Optional[str] = None) -> SpeechSynthesisResult:
        """
        Synthesize text into speech audio.
        
        Args:
            text: The text to synthesize.
            language: Optional language hint (e.g. 'en', 'hi').
            
        Returns:
            SpeechSynthesisResult containing audio bytes and mime type.
            
        Raises:
            TTSProviderError: Base class for TTS errors.
        """
        ...
