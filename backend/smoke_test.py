import sys
import os

# Ensure backend root is in PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.config.settings import settings
from app.ai_interview.llm_infrastructure.adapters.openai_adapter import OpenAICompatibleAdapter
import httpx

def run_smoke_test():
    print(f"GROQ_API_KEY configured: {'YES' if settings.GROQ_API_KEY else 'NO'}")
    
    if not settings.GROQ_API_KEY:
        print("Cannot run smoke test: GROQ_API_KEY is not set.")
        return
        
    print("Instantiating OpenAICompatibleAdapter...")
    adapter = OpenAICompatibleAdapter()
    
    print(f"Base URL: {adapter.base_url}")
    print(f"Model: {adapter.model}")
    print("Sending smoke-test request...")
    
    try:
        response = adapter.generate_text(
            system_prompt="You are a harmless test bot.",
            user_prompt="Reply with exactly: IntelliHire Groq connection successful"
        )
        print("\n=== MODEL RESPONSE ===")
        print(response)
        print("======================\n")
        
    except Exception as e:
        print(f"\nSmoke test failed: {e}")
        # Try to extract the httpx exception if it's chained
        if hasattr(e, '__cause__') and isinstance(e.__cause__, httpx.HTTPStatusError):
            print(f"Response Body: {e.__cause__.response.text}")

if __name__ == "__main__":
    run_smoke_test()
