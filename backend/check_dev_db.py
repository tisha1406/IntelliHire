import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def check():
    client = AsyncIOMotorClient("mongodb://127.0.0.1:27017")
    db = client["intellihire"]
    
    modes_count = await db["interview_mode_definitions"].count_documents({})
    resumes_count = await db["resume_analyses"].count_documents({})
    
    print(f"interview_mode_definitions: {modes_count}")
    print(f"resume_analyses: {resumes_count}")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(check())
