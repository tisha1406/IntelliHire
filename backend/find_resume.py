import asyncio
from app.db.mongo import get_database, connect_db, close_db

async def f():
    await connect_db()
    db = get_database()
    cols = await db.list_collection_names()
    print("Collections:", cols)
    
    for col in cols:
        count = await db[col].count_documents({})
        if count > 0:
            doc = await db[col].find_one()
            if 'ats_score' in doc or 'overall_score' in doc:
                print(f"FOUND score in collection: {col}")
            
    await close_db()

asyncio.run(f())
