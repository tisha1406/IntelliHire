import asyncio
from app.db.mongo import connect_db, close_db, get_database
from app.repositories.candidate_repository import CandidateRepository
from app.auth.jwt_handler import create_access_token
import httpx
from bson import ObjectId

async def main():
    await connect_db()
    db = get_database()
    repo = CandidateRepository()
    
    # Create candidate without campaign
    candidate = {
        "email": "test404@example.com",
        "first_name": "Test",
        "last_name": "404",
        "company_id": ObjectId("6a7492a1ba2af4d02d21e4a6")
    }
    candidate_id = await repo.create(candidate)
    
    token = create_access_token(
        user_id="test404@example.com",
        role="candidate",
        candidate_id=str(candidate_id),
        company_id="6a7492a1ba2af4d02d21e4a6"
    )
    
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "http://localhost:8000/api/candidate/practice/start",
            headers={"Authorization": f"Bearer {token}"}
        )
        print("Status:", resp.status_code)
        print("Body:", resp.text)
        
    await close_db()

if __name__ == "__main__":
    asyncio.run(main())
