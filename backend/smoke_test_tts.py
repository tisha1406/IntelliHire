import sys
import os
import asyncio

# Ensure backend root is in PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.config.settings import settings
from app.ai_interview.speech_infrastructure.tts.sarvam_bulbul_adapter import SarvamBulbulAdapter

async def run_smoke_test():
    print(f"SARVAM_API_KEY configured: {'YES' if settings.SARVAM_API_KEY else 'NO'}")
    print(f"SARVAM_TTS_MODEL: {settings.SARVAM_TTS_MODEL}")
    print(f"SARVAM_TTS_LANGUAGE: {settings.SARVAM_TTS_LANGUAGE}")
    print(f"SARVAM_TTS_SPEAKER: {settings.SARVAM_TTS_SPEAKER}")
    
    if not settings.SARVAM_API_KEY:
        print("Cannot run smoke test: SARVAM_API_KEY is not set.")
        return
        
    print("\nInstantiating SarvamBulbulAdapter...")
    tts_adapter = SarvamBulbulAdapter(
        api_key=settings.SARVAM_API_KEY, 
        model=settings.SARVAM_TTS_MODEL,
        language_code=settings.SARVAM_TTS_LANGUAGE,
        speaker=settings.SARVAM_TTS_SPEAKER
    )
    
    text = "Tell me about a project you have worked on recently."
    print(f"Synthesizing text: '{text}'")
    
    try:
        tts_result = await tts_adapter.synthesize(text)
        print("\n=== MODEL RESPONSE ===")
        print(f"Provider: {tts_result.provider}")
        print(f"MIME Type: {tts_result.mime_type}")
        print(f"Duration MS: {tts_result.duration_ms}")
        print("======================\n")
        
        audio_bytes = tts_result.audio_bytes
        output_file = "tts_output.wav"
        
        with open(output_file, "wb") as f:
            f.write(audio_bytes)
            
        file_size = os.path.getsize(output_file)
        print(f"Audio saved to {output_file}. Size: {file_size} bytes")
        
        # Verify valid WAV header (RIFF)
        with open(output_file, "rb") as f:
            header = f.read(4)
            if header == b"RIFF":
                print("Header validation: SUCCESS (Valid RIFF/WAV header found)")
            else:
                print(f"Header validation: FAILED (Unknown header: {header})")
        
    except Exception as e:
        print(f"\nTTS smoke test failed: {e}")
        import httpx
        if hasattr(e, '__cause__') and isinstance(e.__cause__, httpx.HTTPStatusError):
            print(f"Response Body: {e.__cause__.response.text}")

if __name__ == "__main__":
    asyncio.run(run_smoke_test())
