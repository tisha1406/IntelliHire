import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def update_company():
    client = AsyncIOMotorClient('mongodb://localhost:27017')
    db = client['intellihire']
    await db.companies.update_one(
        {'general.name': 'Infosys'},
        {'$set': {'allowed_languages': ['English', 'Hindi'], 'allowed_voices': ['shubh', 'simran', 'rohan', 'ishita', 'sunny']}}
    )
    print('Updated Infosys entitlements')

asyncio.run(update_company())
