import asyncio
# pyrefly: ignore [missing-import]
from motor.motor_asyncio import AsyncIOMotorClient

async def check():
    client = AsyncIOMotorClient('mongodb://127.0.0.1:27017/intellihire')
    db = client.get_default_database()
    
    missing_email_companies = await db.companies.find({
        "$or": [
            {"general.contact_email": None},
            {"general.contact_email": {"$exists": False}}
        ]
    }).to_list(length=100)
    
    print(f"Found {len(missing_email_companies)} companies with null or missing general.contact_email:")
    for c in missing_email_companies:
        print(f" - {c.get('name', 'Unknown')}")
        
    client.close()

if __name__ == "__main__":
    asyncio.run(check())
