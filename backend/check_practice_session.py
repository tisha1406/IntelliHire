import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import json
from datetime import datetime

class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
async def main():
    client = AsyncIOMotorClient('mongodb://localhost:27017')
    db = client['intellihire']
    count = await db['interview_sessions'].count_documents({'mode_id': 'practice'})
    print(f"Number of practice sessions: {count}")

asyncio.run(main())
