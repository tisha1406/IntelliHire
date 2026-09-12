class LLMProviderError(Exception):
    """Base exception for all LLM provider issues."""
    pass

class LLMTransientError(LLMProviderError):
    """Raised for retryable errors (429, 5xx, timeouts)."""
    pass

class LLMFatalError(LLMProviderError):
    """Raised for non-retryable errors (400, 401, 403, configuration issues)."""
    pass

class LLMGenerationError(LLMProviderError):
    """Raised when the LLM provider fails to generate a response (general)."""
    pass

class LLMValidationError(LLMProviderError):
    """Raised when the generated output cannot be parsed or validated against the requested schema."""
    pass
