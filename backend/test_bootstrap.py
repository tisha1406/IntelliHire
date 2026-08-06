import asyncio
from app.db.mongo import connect_db, close_db
from app.db.bootstrap import bootstrap_platform

async def run_bootstrap():
    await connect_db()
    await bootstrap_platform()
    await close_db()

if __name__ == "__main__":
    asyncio.run(run_bootstrap())
