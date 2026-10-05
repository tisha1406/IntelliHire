import asyncio
from app.db.mongo import connect_db, close_db, get_database

async def check():
    await connect_db()
    db = get_database()
    col = db.get_collection("interview_mode_definitions")
    docs = await col.find({}).to_list(length=100)
    print(f"Found {len(docs)} modes in 'interview_mode_definitions':")
    for d in docs:
        print(d)
    
    col2 = db.get_collection("interview_modes")
    docs2 = await col2.find({}).to_list(length=100)
    print(f"Found {len(docs2)} modes in 'interview_modes':")
    for d in docs2:
        print(d)
    
    await close_db()

asyncio.run(check())
