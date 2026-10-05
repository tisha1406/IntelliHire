import asyncio
from app.db.mongo import get_database, connect_db, close_db

async def f():
    await connect_db()
    c = await get_database().get_collection('candidates').find_one()
    print("CANDIDATE ID:", str(c['_id']))
    print("COMPANY ID:", str(c['company_id']))
    print("CAMPAIGN ID:", str(c['campaign_id']))
    await close_db()

asyncio.run(f())
