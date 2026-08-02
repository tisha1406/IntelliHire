import asyncio
from app.db.mongo import connect_db, close_db, get_database

async def main():
    await connect_db()
    db = get_database()
    companies = await db['companies'].find({}).to_list(length=None)
    print(f"Total companies: {len(companies)}")
    for c in companies:
        print(c)
    await close_db()

if __name__ == "__main__":
    asyncio.run(main())
