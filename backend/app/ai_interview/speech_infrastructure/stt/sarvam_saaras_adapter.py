import os
import httpx
import logging
import time
from typing import Optional

from app.ai_interview.speech_infrastructure.interfaces import SpeechToTextProvider
from app.ai_interview.speech_infrastructure.schemas import TranscriptionResult
from app.ai_interview.speech_infrastructure.exceptions import STTTransientError, STTFatalError

logger = logging.getLogger(__name__)

class SarvamSaarasAdapter(SpeechToTextProvider):
    """
    STT Provider implementation using Sarvam AI Saaras.
    Converts audio bytes into transcript text securely without mutating any domain state.
    """
    
    def __init__(
        self, 
        api_key: Optional[str] = None, 
        model: str = "saaras:v1",
        base_url: str = "https://api.sarvam.ai",
        timeout: float = 30.0
    ):
        self.api_key = api_key or os.environ.get("SARVAM_API_KEY", "dummy_key")
        self.model = model
        self.base_url = base_url
        self.timeout = timeout
        self.headers = {
            "api-subscription-key": self.api_key
        }

    async def transcribe(self, audio_bytes: bytes, mime_type: str) -> TranscriptionResult:
        """
        Calls Sarvam Saaras API.
        """
        # Sarvam expects common extensions: wav, mp3, mp4, etc.
        extension = "webm"
        if "mp4" in mime_type:
            extension = "mp4"
        elif "mp3" in mime_type:
            extension = "mp3"
        elif "wav" in mime_type:
            extension = "wav"
        elif "mpeg" in mime_type:
            extension = "mp3"
        elif "ogg" in mime_type:
            extension = "ogg"
        
        file_tuple = (f"audio.{extension}", audio_bytes, mime_type)
        files = {"file": file_tuple}
        
        # Sarvam speech-to-text API:
        # endpoint: /speech-to-text-translate for English, or /speech-to-text
        # We will use /speech-to-text as standard
        data = {
            "model": self.model,
            # optional parameters based on Sarvam's API
        }
        
        start_time = time.time()
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/speech-to-text",
                    headers=self.headers,
                    files=files,
                    data=data
                )
                
                if response.status_code == 429:
                    raise STTTransientError("Sarvam Saaras rate limit exceeded")
                if response.status_code >= 500:
                    raise STTTransientError(f"Sarvam Saaras server error: {response.status_code}")
                if response.status_code == 401 or response.status_code == 403:
                    raise STTFatalError("Sarvam Saaras authentication failed")
                if response.status_code >= 400:
                    raise STTFatalError(f"Sarvam Saaras client error: {response.text}")
                    
                response.raise_for_status()
                result_json = response.json()
                
                # Assuming Sarvam's response contains a 'transcript' field
                transcript = result_json.get("transcript", "")
                language = result_json.get("language_code")
                
                duration_ms = int((time.time() - start_time) * 1000)
                
                return TranscriptionResult(
                    transcript=transcript.strip(),
                    language=language,
                    duration_ms=duration_ms,
                    provider="sarvam"
                )
                
        except httpx.TimeoutException as e:
            raise STTTransientError(f"Sarvam Saaras timeout: {e}")
        except httpx.RequestError as e:
            raise STTTransientError(f"Sarvam Saaras network error: {e}")
