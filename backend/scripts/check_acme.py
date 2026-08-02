import asyncio
import json
# pyrefly: ignore [missing-import]
from bson import json_util
# pyrefly: ignore [missing-import]
from motor.motor_asyncio import AsyncIOMotorClient

async def check():
    client = AsyncIOMotorClient('mongodb://127.0.0.1:27017/intellihire')
    db = client.get_default_database()
    
    docs = await db.companies.find({
        "$or": [
            {"name": "Acme Technologies"},
            {"general.name": "Acme Technologies"}
        ]
    }).to_list(length=100)
    
    print(json.dumps(docs, default=json_util.default, indent=2))
    client.close()

if __name__ == "__main__":
    asyncio.run(check())
