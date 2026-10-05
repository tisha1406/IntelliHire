import sys
import os
from pydantic import BaseModel

# Ensure backend root is in PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.config.settings import settings
from app.ai_interview.llm_infrastructure.adapters.openai_adapter import OpenAICompatibleAdapter

class SmokeTestResult(BaseModel):
    status: str
    message: str

def run_smoke_test():
    print(f"GROQ_API_KEY configured: {'YES' if settings.GROQ_API_KEY else 'NO'}")
    
    if not settings.GROQ_API_KEY:
        print("Cannot run smoke test: GROQ_API_KEY is not set.")
        return
        
    print("Instantiating OpenAICompatibleAdapter...")
    adapter = OpenAICompatibleAdapter()
    
    print(f"Base URL: {adapter.base_url}")
    print(f"Model: {adapter.model}")
    print("Sending structured smoke-test request...")
    
    try:
        response_obj = adapter.generate_structured(
            system_prompt="You are a harmless test bot. Reply strictly with the requested structure.",
            user_prompt="Return status as 'success' and message as 'IntelliHire structured Groq connection successful'",
            response_model=SmokeTestResult
        )
        print("\n=== STRUCTURED MODEL RESPONSE ===")
        print(f"Type: {type(response_obj)}")
        print(f"Status: {response_obj.status}")
        print(f"Message: {response_obj.message}")
        print("======================\n")
        
    except Exception as e:
        print(f"\nStructured smoke test failed: {e}")

if __name__ == "__main__":
    run_smoke_test()
