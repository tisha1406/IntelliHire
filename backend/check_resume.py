import asyncio
from app.db.mongo import get_database, connect_db, close_db

async def f():
    await connect_db()
    
    # 1. List candidates
    print("=== Candidates ===")
    async for c in get_database().get_collection('candidates').find():
        print(f"ID: {c['_id']}, Name: {c.get('name')}")
        
    # 2. List resume_analyses
    print("\n=== Resume Analyses ===")
    async for r in get_database().get_collection('resume_analyses').find():
        print(f"ID: {r['_id']}, Candidate ID: {r.get('candidate_id')} (Type: {type(r.get('candidate_id'))})")
        
    await close_db()

asyncio.run(f())
