import asyncio
# pyrefly: ignore [missing-import]
from motor.motor_asyncio import AsyncIOMotorClient

async def run_cleanup():
    client = AsyncIOMotorClient('mongodb://127.0.0.1:27017/intellihire')
    db = client.get_default_database()
    
    result = await db.companies.delete_many({
        "$or": [
            {"general.contact_email": None},
            {"general.contact_email": {"$exists": False}}
        ]
    })
    print(f"Deleted {result.deleted_count} invalid flat companies.")
    client.close()

if __name__ == "__main__":
    asyncio.run(run_cleanup())
