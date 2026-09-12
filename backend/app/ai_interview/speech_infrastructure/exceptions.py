class STTProviderError(Exception):
    """Base exception for all speech infrastructure errors."""
    pass

class STTTransientError(STTProviderError):
    """
    Retryable errors: timeout, rate limiting, transient 5xx from provider.
    """
    pass

class STTFatalError(STTProviderError):
    """
    Non-retryable errors: invalid credentials, malformed audio, unsupported format.
    """
    pass

class STTValidationError(STTProviderError):
    """
    Validation error on the returned transcript (e.g. empty, whitespace).
    """
    pass

class TTSProviderError(Exception):
    """Base exception for all TTS infrastructure errors."""
    pass

class TTSTransientError(TTSProviderError):
    """
    Retryable errors: timeout, rate limiting, transient 5xx from provider.
    """
    pass

class TTSFatalError(TTSProviderError):
    """
    Non-retryable errors: invalid credentials, unsupported text format, unsupported voice.
    """
    pass
