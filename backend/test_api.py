import asyncio
import httpx
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from app.auth.jwt_handler import create_access_token

async def test_campaign_creation():
    token = create_access_token(
        user_id="6a7492a1ba2af4d02d21e4a6",
        role="COMPANY",
    )
    
    async with httpx.AsyncClient() as client:
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "name": "Test Campaign",
            "department": "Engineering",
            "location": "Remote",
            "deadline": "2024-12-31",
            "salary": "100k",
            "description": "Test",
            "employment_type": "Full-time",
            "requirements": [{"skill": "Python", "criticality": "required"}],
            "interview_type": "mixed",
            "strategy_id": "fixed_coverage",
            "interview_settings": {
                "duration": 45,
                "strictness": "medium",
                "type": "mixed"
            },
            "mixed_composition": {
                "technical": 0.25,
                "resume_experience": 0.25,
                "hr_behavioral": 0.25,
                "situational_case": 0.25
            },
            "budget_override": {"target_questions": 10},
            "difficulty_band": "medium",
            "language": "English",
            "voice_id": "ritu"
        }
        
        resp = await client.post(
            "http://localhost:8000/company/campaigns",
            headers=headers,
            json=payload,
            follow_redirects=True
        )
        
        print("Status POST:", resp.status_code)
        print("Response POST:", resp.text)

asyncio.run(test_campaign_creation())
