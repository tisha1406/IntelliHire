import pytest
from unittest.mock import patch, MagicMock
import httpx
from app.ai_interview.speech_infrastructure.stt.sarvam_saaras_adapter import SarvamSaarasAdapter
from app.ai_interview.speech_infrastructure.schemas import TranscriptionResult
from app.ai_interview.speech_infrastructure.exceptions import STTTransientError, STTFatalError
from app.ai_interview.speech_infrastructure.resilience import STTResiliencePolicy

@pytest.fixture
def adapter():
    return SarvamSaarasAdapter(api_key="test_key", model="saaras:v1")

@pytest.mark.asyncio
async def test_sarvam_stt_success(adapter):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"transcript": "hello world", "language_code": "en-IN"}
    
    with patch("httpx.AsyncClient.post", return_value=mock_response):
        result = await adapter.transcribe(b"dummy audio", "audio/webm")
        
        assert isinstance(result, TranscriptionResult)
        assert result.transcript == "hello world"
        assert result.language == "en-IN"
        assert result.provider == "sarvam"
        assert result.duration_ms >= 0

@pytest.mark.asyncio
async def test_sarvam_stt_rate_limit(adapter):
    mock_response = MagicMock()
    mock_response.status_code = 429
    
    with patch("httpx.AsyncClient.post", return_value=mock_response):
        with pytest.raises(STTTransientError) as exc:
            await adapter.transcribe(b"dummy", "audio/webm")
        assert "rate limit" in str(exc.value)

@pytest.mark.asyncio
async def test_sarvam_stt_fatal_auth_error(adapter):
    mock_response = MagicMock()
    mock_response.status_code = 401
    
    with patch("httpx.AsyncClient.post", return_value=mock_response):
        with pytest.raises(STTFatalError) as exc:
            await adapter.transcribe(b"dummy", "audio/webm")
        assert "authentication failed" in str(exc.value)

@pytest.mark.asyncio
async def test_sarvam_stt_resilience_success_after_retry(adapter):
    # Mock first failure, then success
    mock_fail = MagicMock()
    mock_fail.status_code = 500
    
    mock_success = MagicMock()
    mock_success.status_code = 200
    mock_success.json.return_value = {"transcript": "recovered", "language_code": "hi"}
    
    responses = [mock_fail, mock_success]
    
    async def mock_post(*args, **kwargs):
        return responses.pop(0)
        
    policy = STTResiliencePolicy(max_attempts=3, base_delay=0.01)
    
    with patch("httpx.AsyncClient.post", side_effect=mock_post):
        result = await policy.execute(adapter.transcribe, b"dummy", "audio/wav")
        assert result.transcript == "recovered"

@pytest.mark.asyncio
async def test_sarvam_stt_resilience_exhaustion(adapter):
    mock_fail = MagicMock()
    mock_fail.status_code = 502
    
    async def mock_post(*args, **kwargs):
        return mock_fail
        
    policy = STTResiliencePolicy(max_attempts=2, base_delay=0.01)
    
    with patch("httpx.AsyncClient.post", side_effect=mock_post):
        with pytest.raises(STTTransientError):
            await policy.execute(adapter.transcribe, b"dummy", "audio/wav")
