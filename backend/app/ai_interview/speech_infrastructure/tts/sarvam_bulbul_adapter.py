import os
import httpx
import logging
import time
from typing import Optional

from app.ai_interview.speech_infrastructure.interfaces import TextToSpeechProvider
from app.ai_interview.speech_infrastructure.schemas import SpeechSynthesisResult
from app.ai_interview.speech_infrastructure.exceptions import TTSTransientError, TTSFatalError

logger = logging.getLogger(__name__)

class SarvamBulbulAdapter(TextToSpeechProvider):
    """
    TTS Provider implementation using Sarvam AI Bulbul.
    Converts authoritative text into audio bytes securely.
    """
    
    def __init__(
        self, 
        api_key: Optional[str] = None, 
        model: str = "bulbul:v1",
        base_url: str = "https://api.sarvam.ai",
        timeout: float = 30.0
    ):
        self.api_key = api_key or os.environ.get("SARVAM_API_KEY", "dummy_key")
        self.model = model
        self.base_url = base_url
        self.timeout = timeout
        self.headers = {
            "api-subscription-key": self.api_key,
            "Content-Type": "application/json"
        }

    async def synthesize(self, text: str, language: Optional[str] = None) -> SpeechSynthesisResult:
        """
        Calls Sarvam Bulbul API to synthesize speech.
        """
        if not text or not text.strip():
            raise TTSFatalError("Cannot synthesize empty text")
            
        data = {
            "inputs": [text.strip()],
            "target_language_code": language or "hi-IN",
            "speaker": "meera", # Can be configured
            "pitch": 0,
            "pace": 1.0,
            "loudness": 1.5,
            "speech_sample_rate": 8000,
            "enable_preprocessing": True,
            "model": self.model
        }
        
        start_time = time.time()
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/text-to-speech",
                    headers=self.headers,
                    json=data
                )
                
                if response.status_code == 429:
                    raise TTSTransientError("Sarvam Bulbul rate limit exceeded")
                if response.status_code >= 500:
                    raise TTSTransientError(f"Sarvam Bulbul server error: {response.status_code}")
                if response.status_code == 401 or response.status_code == 403:
                    raise TTSFatalError("Sarvam Bulbul authentication failed")
                if response.status_code >= 400:
                    raise TTSFatalError(f"Sarvam Bulbul client error: {response.text}")
                    
                response.raise_for_status()
                
                result_json = response.json()
                
                # Sarvam API returns a base64 encoded audio string in 'audios' list
                audios = result_json.get("audios", [])
                if not audios:
                    raise TTSFatalError("Sarvam Bulbul returned no audio data")
                
                base64_audio = audios[0]
                import base64
                audio_bytes = base64.b64decode(base64_audio)
                
                duration_ms = int((time.time() - start_time) * 1000)
                
                return SpeechSynthesisResult(
                    audio_bytes=audio_bytes,
                    mime_type="audio/wav",
                    provider="sarvam",
                    duration_ms=duration_ms
                )
                
        except httpx.TimeoutException as e:
            raise TTSTransientError(f"Sarvam Bulbul timeout: {e}")
        except httpx.RequestError as e:
            raise TTSTransientError(f"Sarvam Bulbul network error: {e}")
