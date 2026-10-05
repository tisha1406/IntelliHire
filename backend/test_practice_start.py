import asyncio
import httpx
from datetime import timedelta
from app.auth.jwt_handler import create_access_token

async def test_endpoint():
    # 1. Generate a mock token for candidate
    token = create_access_token(
        user_id="hr@acme.dev",
        role="candidate",
        candidate_id="6a7a755cd895398ceb628a37",
        company_id="6a7492a1ba2af4d02d21e4a6",
        campaign_id="6a749346ba2af4d02d21e4a8"
    )
    
    # 2. Make the request
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/api/candidate/practice/start",
            headers={"Authorization": f"Bearer {token}"}
        )
        print("STATUS:", response.status_code)
        print("RESPONSE:", response.json())

asyncio.run(test_endpoint())
