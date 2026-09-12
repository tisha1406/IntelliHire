"""
Phase 11 — Speech Infrastructure Boundary

Isolates Speech-to-Text and Text-to-Speech logic from the deterministic interview engine.
"""

from .interfaces import SpeechToTextProvider, TextToSpeechProvider
from .schemas import TranscriptionResult, SpeechSynthesisResult
from .exceptions import STTProviderError, STTTransientError, STTFatalError, STTValidationError, TTSProviderError, TTSTransientError, TTSFatalError
from .resilience import STTResiliencePolicy, TTSResiliencePolicy
from .stt.validator import STTValidator
from .stt.provider_adapter import OpenAIWhisperAdapter

__all__ = [
    "SpeechToTextProvider",
    "TextToSpeechProvider",
    "TranscriptionResult",
    "SpeechSynthesisResult",
    "STTProviderError",
    "STTTransientError",
    "STTFatalError",
    "STTValidationError",
    "TTSProviderError",
    "TTSTransientError",
    "TTSFatalError",
    "STTResiliencePolicy",
    "TTSResiliencePolicy",
    "STTValidator",
    "OpenAIWhisperAdapter"
]
