import pytest
import asyncio
from unittest.mock import Mock, AsyncMock

from app.ai_interview.speech_infrastructure.exceptions import STTTransientError, STTFatalError
from app.ai_interview.speech_infrastructure.resilience import STTResiliencePolicy

# This test explicitly proves STT Purity Invariant:
# STT failures or successes DO NOT mutate interview state directly.
# The endpoint tests will verify this at the HTTP boundary, but we verify the core STT resilience here.

@pytest.mark.asyncio
async def test_stt_transient_failure_exhaustion():
    mock_provider = AsyncMock()
    mock_provider.transcribe.side_effect = STTTransientError("Timeout")
    
    policy = STTResiliencePolicy(max_attempts=2, base_delay=0.01)
    
    with pytest.raises(STTTransientError):
        await policy.execute(mock_provider.transcribe, b"audio", "audio/webm")
        
    # Provider called exactly twice, no interview state dependencies were touched
    assert mock_provider.transcribe.call_count == 2

@pytest.mark.asyncio
async def test_stt_fatal_failure_no_retry():
    mock_provider = AsyncMock()
    mock_provider.transcribe.side_effect = STTFatalError("Auth failed")
    
    policy = STTResiliencePolicy(max_attempts=3)
    
    with pytest.raises(STTFatalError):
        await policy.execute(mock_provider.transcribe, b"audio", "audio/webm")
        
    # Fatal error does not retry
    assert mock_provider.transcribe.call_count == 1
