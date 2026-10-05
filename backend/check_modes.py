import asyncio
from app.db.mongo import connect_db, get_database, close_db

async def check():
    await connect_db()
    db = get_database()
    docs = await db["interview_mode_definitions"].find({}).to_list(100)
    print(f"Total documents: {len(docs)}")
    for doc in docs:
        print(f"Mode ID: {doc.get('mode_id')}, Status: {doc.get('status')}")
    await close_db()

if __name__ == "__main__":
    asyncio.run(check())
