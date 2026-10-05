import asyncio
from app.db.mongo import get_database, connect_db, close_db

async def f():
    await connect_db()
    docs = await get_database().get_collection('resume_analyses').find({}).to_list(10)
    print(f"Total documents: {len(docs)}")
    for d in docs:
        print(f"ID: {d['_id']}, candidate_id: {d.get('candidate_id')}")
    await close_db()

asyncio.run(f())
