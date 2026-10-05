import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def main():
    client = AsyncIOMotorClient('mongodb://localhost:27017')
    db = client['intellihire']
    sessions = await db['interview_sessions'].find({}).sort('created_at', -1).to_list(1)
    for s in sessions:
        print(s)

asyncio.run(main())
