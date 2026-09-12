import os
import httpx
import logging
import io
from typing import Optional
from app.ai_interview.speech_infrastructure.interfaces import SpeechToTextProvider
from app.ai_interview.speech_infrastructure.schemas import TranscriptionResult
from app.ai_interview.speech_infrastructure.exceptions import STTTransientError, STTFatalError

logger = logging.getLogger(__name__)

class OpenAIWhisperAdapter(SpeechToTextProvider):
    """
    OpenAI Whisper implementation of SpeechToTextProvider.
    Uses httpx for the external API call.
    """
    
    def __init__(self, api_key: Optional[str] = None, base_url: str = "https://api.openai.com/v1"):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY", "dummy_key")
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {self.api_key}"
        }

    async def transcribe(self, audio_bytes: bytes, mime_type: str) -> TranscriptionResult:
        """
        Calls OpenAI Whisper API.
        Does not mutate any domain state.
        """
        # Defensive map of mime types to whisper-allowed extensions
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
        data = {"model": "whisper-1"}
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.base_url}/audio/transcriptions",
                    headers=self.headers,
                    files=files,
                    data=data
                )
                
                response.raise_for_status()
                response_data = response.json()
                
                transcript = response_data.get("text", "")
                duration_ms = int(response.elapsed.total_seconds() * 1000)
                
                logger.info(f"OpenAIWhisperAdapter: transcription successful in {duration_ms}ms")
                
                return TranscriptionResult(
                    transcript=transcript,
                    language=response_data.get("language"),
                    duration_ms=duration_ms,
                    provider="OpenAIWhisper"
                )
                
        except httpx.HTTPStatusError as e:
            status = e.response.status_code
            if status in (429, 500, 502, 503, 504):
                logger.warning(f"Transient HTTP {status} from Whisper.")
                raise STTTransientError(f"Transient provider error: {status}") from e
            elif status == 401 or status == 403:
                logger.error(f"Fatal HTTP {status} from Whisper: Auth Error.")
                raise STTFatalError("Provider authentication failed.") from e
            elif status == 400:
                logger.error(f"Fatal HTTP 400 from Whisper: Bad Request/Unsupported Media.")
                raise STTFatalError("Unsupported media or bad request.") from e
            else:
                raise STTFatalError(f"Fatal provider error: {status}") from e
        except httpx.TimeoutException as e:
            logger.warning("Timeout communicating with Whisper.")
            raise STTTransientError("Provider timeout") from e
        except httpx.RequestError as e:
            logger.error("Network error communicating with Whisper.")
            raise STTTransientError("Provider network error") from e
        except Exception as e:
            logger.error(f"Unexpected error communicating with Whisper: {e}")
            raise STTFatalError(f"Unexpected provider error: {e}") from e
