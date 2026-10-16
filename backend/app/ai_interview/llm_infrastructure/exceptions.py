class LLMProviderError(Exception):
    """Base exception for all LLM provider issues."""
    pass

class LLMTransientError(LLMProviderError):
    """
    Raised for retryable errors (429, 5xx, timeouts).

    retry_after_seconds: when the provider tells us exactly how long until
    its rate-limit window resets (Groq's `x-ratelimit-reset-tokens` response
    header on a 429), callers should wait that long rather than guessing --
    a fixed short delay is often shorter than the provider's own window and
    the retry just gets rate-limited again. None when no such hint exists
    (e.g. a 5xx or network timeout).
    """
    def __init__(self, message: str, retry_after_seconds: float | None = None):
        super().__init__(message)
        self.retry_after_seconds = retry_after_seconds

class LLMFatalError(LLMProviderError):
    """Raised for non-retryable errors (400, 401, 403, configuration issues)."""
    pass

class LLMGenerationError(LLMProviderError):
    """Raised when the LLM provider fails to generate a response (general)."""
    pass

class LLMValidationError(LLMProviderError):
    """Raised when the generated output cannot be parsed or validated against the requested schema."""
    pass
