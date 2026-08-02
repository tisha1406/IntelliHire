import asyncio
import json
from bson import json_util
from motor.motor_asyncio import AsyncIOMotorClient

async def investigate():
    client = AsyncIOMotorClient('mongodb://127.0.0.1:27017/intellihire')
    db = client.get_default_database()
    
    docs = await db.companies.find({}).to_list(length=None)
    
    print(f"Total companies in DB: {len(docs)}")
    
    for doc in docs:
        print("--------------------------------------------------")
        print(f"_id: {doc.get('_id')}")
        print(f"general.name: {doc.get('general', {}).get('name') if isinstance(doc.get('general'), dict) else doc.get('name')}")
        print(f"general.contact_email: {doc.get('general', {}).get('contact_email') if isinstance(doc.get('general'), dict) else doc.get('contact_email')}")
        print(f"status: {doc.get('status')} | subscription.status: {doc.get('subscription', {}).get('status') if isinstance(doc.get('subscription'), dict) else 'N/A'}")
        print(f"deleted_at: {doc.get('deleted_at')}")
        print(f"created_at: {doc.get('created_at')}")
        print(f"updated_at: {doc.get('updated_at')}")
        
    client.close()

if __name__ == "__main__":
    asyncio.run(investigate())
