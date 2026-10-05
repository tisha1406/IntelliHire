import asyncio
from app.db.mongo import get_database, connect_db, close_db
import json
from bson import json_util

async def f():
    await connect_db()
    db = get_database()
    cols = await db.list_collection_names()
    
    found_any = False
    for col in cols:
        docs = await db[col].find({
            "$or": [
                {"ats_score": {"$exists": True}},
                {"overall_score": {"$exists": True}}
            ]
        }).to_list(None)
        
        if docs:
            print(f"\n--- FOUND in {col} ---")
            for doc in docs:
                found_any = True
                print("KEYS:", list(doc.keys()))
                if 'candidate_id' in doc:
                    print("CANDIDATE_ID:", doc['candidate_id'], type(doc['candidate_id']))
                else:
                    print("NO candidate_id field!")
                
    if not found_any:
        print("NO DOCUMENTS FOUND WITH ats_score or overall_score in ANY COLLECTION!")
    
    await close_db()

asyncio.run(f())
