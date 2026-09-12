import pytest
from app.ai_interview.llm_infrastructure.resilience import ResiliencePolicy
from app.ai_interview.llm_infrastructure.exceptions import (
    LLMTransientError, LLMFatalError, LLMValidationError
)

def test_retryable_failure_succeeds_eventually():
    attempts = 0
    def mock_api():
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            raise LLMTransientError("timeout")
        return "success"
        
    res = ResiliencePolicy.execute_with_retry(mock_api, max_attempts=3, base_delay_seconds=0.01)
    assert res == "success"
    assert attempts == 3

def test_retry_exhaustion_raises():
    attempts = 0
    def mock_api():
        nonlocal attempts
        attempts += 1
        raise LLMTransientError("timeout")
        
    with pytest.raises(LLMTransientError):
        ResiliencePolicy.execute_with_retry(mock_api, max_attempts=3, base_delay_seconds=0.01)
    assert attempts == 3

def test_non_retryable_failure_raises_immediately():
    attempts = 0
    def mock_api():
        nonlocal attempts
        attempts += 1
        raise LLMFatalError("401 Unauthorized")
        
    with pytest.raises(LLMFatalError):
        ResiliencePolicy.execute_with_retry(mock_api, max_attempts=3, base_delay_seconds=0.01)
    assert attempts == 1  # No retries on fatal errors

def test_validation_failure_retries():
    attempts = 0
    def mock_api():
        nonlocal attempts
        attempts += 1
        if attempts < 2:
            raise LLMValidationError("bad json")
        return "success"
        
    res = ResiliencePolicy.execute_with_retry(mock_api, max_attempts=2, base_delay_seconds=0.01)
    assert res == "success"
    assert attempts == 2
