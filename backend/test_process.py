import asyncio
from app.db.mongo import connect_db, close_db
from app.services.resume_processing_service import ResumeProcessingService

async def test():
    await connect_db()
    service = ResumeProcessingService()
    await service.process_resume(
        candidate_id="6a7a755cd895398ceb628a37",
        company_id="6a7492a1ba2af4d02d21e4a6",
        campaign_id="6a749346ba2af4d02d21e4a8",
        file_bytes=b"dummy resume content",
        filename="resume.pdf"
    )
    print("Done")
    await close_db()

asyncio.run(test())
