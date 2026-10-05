import asyncio
from app.db.mongo import connect_db, close_db
from app.repositories.interview_mode_repository import InterviewModeRepository

async def test():
    await connect_db()
    repo = InterviewModeRepository()
    doc = await repo.get_by_mode_id('balanced')
    print('MODE:', doc)
    await close_db()

asyncio.run(test())
