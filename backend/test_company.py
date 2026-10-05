import asyncio
import json
from bson import json_util
from motor.motor_asyncio import AsyncIOMotorClient

async def main():
    client = AsyncIOMotorClient('mongodb://localhost:27017')
    db = client['intellihire']
    comp = await db.companies.find_one()
    print(json.dumps(comp, default=json_util.default, indent=2))
    
    camps = await db.campaigns.count_documents({"company_id": comp["_id"]})
    print("Campaign count before POST:", camps)

asyncio.run(main())
