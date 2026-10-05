import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def update_campaigns():
    client = AsyncIOMotorClient('mongodb://localhost:27017')
    db = client['intellihire']
    await db.campaigns.update_many(
        {'assigned_recruiter_ids': None},
        {'$set': {'assigned_recruiter_ids': []}}
    )
    print('Updated campaigns')

asyncio.run(update_campaigns())
