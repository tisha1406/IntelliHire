import asyncio
from app.db.mongo import connect_db, get_database, close_db

async def check():
    await connect_db()
    db = get_database()
    c = await db.candidates.find_one()
    print('Candidate:', c.get('campaign_id') if c else 'None')
    await close_db()

if __name__ == "__main__":
    asyncio.run(check())
