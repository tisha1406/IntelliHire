import asyncio
from app.db.mongo import connect_db, close_db, client

async def main():
    await connect_db()
    from app.db.mongo import client
    await client.drop_database('intellihire')
    print("Database dropped")
    await close_db()

if __name__ == "__main__":
    asyncio.run(main())
