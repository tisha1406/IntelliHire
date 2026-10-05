import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def check_session():
    client = AsyncIOMotorClient("mongodb://127.0.0.1:27017")
    db = client["intellihire"]
    
    session_id = "78ad842b-959f-433c-a48d-126e928beb6d"
    session = await db["interview_sessions"].find_one({"session_id": session_id})
    
    if session:
        print(f"Exists: YES")
        print(f"State: {session.get('state')}")
        print(f"Candidate ID: {session.get('candidate_id')}")
        print(f"Company ID: {session.get('company_id')}")
        print(f"Campaign ID: {session.get('campaign_id')}")
    else:
        print(f"Exists: NO")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(check_session())
