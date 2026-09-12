import pytest
from unittest.mock import patch, MagicMock
import base64
from app.ai_interview.speech_infrastructure.tts.sarvam_bulbul_adapter import SarvamBulbulAdapter
from app.ai_interview.speech_infrastructure.schemas import SpeechSynthesisResult
from app.ai_interview.speech_infrastructure.exceptions import TTSTransientError, TTSFatalError
from app.ai_interview.speech_infrastructure.resilience import TTSResiliencePolicy

@pytest.fixture
def adapter():
    return SarvamBulbulAdapter(api_key="test_key", model="bulbul:v1")

@pytest.mark.asyncio
async def test_sarvam_tts_success(adapter):
    mock_response = MagicMock()
    mock_response.status_code = 200
    
    # Mock Sarvam's base64 encoded audio list
    fake_audio = b"fake audio content"
    b64_audio = base64.b64encode(fake_audio).decode("utf-8")
    mock_response.json.return_value = {"audios": [b64_audio]}
    
    with patch("httpx.AsyncClient.post", return_value=mock_response):
        result = await adapter.synthesize("Hello world", language="hi-IN")
        
        assert isinstance(result, SpeechSynthesisResult)
        assert result.audio_bytes == fake_audio
        assert result.mime_type == "audio/wav"
        assert result.provider == "sarvam"
        assert result.duration_ms >= 0

@pytest.mark.asyncio
async def test_sarvam_tts_empty_text(adapter):
    with pytest.raises(TTSFatalError) as exc:
        await adapter.synthesize("")
    assert "empty text" in str(exc.value)

@pytest.mark.asyncio
async def test_sarvam_tts_rate_limit(adapter):
    mock_response = MagicMock()
    mock_response.status_code = 429
    
    with patch("httpx.AsyncClient.post", return_value=mock_response):
        with pytest.raises(TTSTransientError) as exc:
            await adapter.synthesize("Hello")
        assert "rate limit" in str(exc.value)

@pytest.mark.asyncio
async def test_sarvam_tts_fatal_auth_error(adapter):
    mock_response = MagicMock()
    mock_response.status_code = 403
    
    with patch("httpx.AsyncClient.post", return_value=mock_response):
        with pytest.raises(TTSFatalError) as exc:
            await adapter.synthesize("Hello")
        assert "authentication failed" in str(exc.value)

@pytest.mark.asyncio
async def test_sarvam_tts_resilience_success_after_retry(adapter):
    mock_fail = MagicMock()
    mock_fail.status_code = 503
    
    mock_success = MagicMock()
    mock_success.status_code = 200
    b64_audio = base64.b64encode(b"recovered").decode("utf-8")
    mock_success.json.return_value = {"audios": [b64_audio]}
    
    responses = [mock_fail, mock_success]
    
    async def mock_post(*args, **kwargs):
        return responses.pop(0)
        
    policy = TTSResiliencePolicy(max_attempts=3, base_delay=0.01)
    
    with patch("httpx.AsyncClient.post", side_effect=mock_post):
        result = await policy.execute(adapter.synthesize, "retry test")
        assert result.audio_bytes == b"recovered"

@pytest.mark.asyncio
async def test_sarvam_tts_missing_audio_data(adapter):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"audios": []}
    
    with patch("httpx.AsyncClient.post", return_value=mock_response):
        with pytest.raises(TTSFatalError) as exc:
            await adapter.synthesize("Hello")
        assert "no audio data" in str(exc.value)
