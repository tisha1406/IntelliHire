import sys
import os
import asyncio

# Ensure backend root is in PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.config.settings import settings
from app.ai_interview.speech_infrastructure.stt.sarvam_saaras_adapter import SarvamSaarasAdapter

async def run_smoke_test():
    print(f"SARVAM_API_KEY configured: {'YES' if settings.SARVAM_API_KEY else 'NO'}")
    print(f"SARVAM_STT_MODEL: {settings.SARVAM_STT_MODEL}")
    print(f"SARVAM_STT_LANGUAGE: {settings.SARVAM_STT_LANGUAGE}")
    
    if not settings.SARVAM_API_KEY:
        print("Cannot run smoke test: SARVAM_API_KEY is not set.")
        return
        
    print("Reading test audio file (speech_test.mp3)...")
    file_path = "speech_test.mp3"
    with open(file_path, "rb") as f:
        audio_bytes = f.read()
    mime_type = "audio/mp3"
    
    print("Instantiating SarvamSaarasAdapter...")
    stt_adapter = SarvamSaarasAdapter(
        api_key=settings.SARVAM_API_KEY, 
        model=settings.SARVAM_STT_MODEL,
        language_code=settings.SARVAM_STT_LANGUAGE
    )
    
    print("Sending smoke-test request to STT...")
    try:
        stt_result = await stt_adapter.transcribe(audio_bytes, mime_type)
        print("\n=== MODEL RESPONSE ===")
        print(f"Provider: {stt_result.provider}")
        print(f"Language: {stt_result.language}")
        print(f"Duration MS: {stt_result.duration_ms}")
        print(f"Transcript: {stt_result.transcript}")
        print("======================\n")
    except Exception as e:
        print(f"\nSTT smoke test failed: {e}")
        import httpx
        if hasattr(e, '__cause__') and isinstance(e.__cause__, httpx.HTTPStatusError):
            print(f"Response Body: {e.__cause__.response.text}")

if __name__ == "__main__":
    asyncio.run(run_smoke_test())
