import pytest
from scripts.seed_dev_data import seed_interview_modes
from app.repositories.interview_mode_repository import InterviewModeRepository
from app.ai_interview.schemas.interview_mode import InterviewModeDefinition
from app.ai_interview.core.enums import InterviewModeStatus

from app.db.mongo import connect_db, close_db

@pytest.mark.asyncio
async def test_seed_interview_modes():
    await connect_db()
    try:
        repo = InterviewModeRepository()
        
        # 1. Clear collection first to ensure clean state
        await repo.collection.delete_many({})
        
        # 2. Run seed
        await seed_interview_modes()
        
        # 3. Verify modes are created
        modes = await repo.get_many({})
        assert len(modes) == 4, f"Expected 4 modes, got {len(modes)}"
        
        mode_ids = {m["mode_id"] for m in modes}
        assert "balanced" in mode_ids
        assert "technical" in mode_ids
        assert "structured" in mode_ids
        assert "deep_technical" in mode_ids
        
        # 4. Verify conformity to schema and status
        for mode in modes:
            # If it parses through Pydantic, it conforms to schema
            parsed_mode = InterviewModeDefinition(**mode)
            assert parsed_mode.status == InterviewModeStatus.PUBLISHED
        
        # 5. Run seed again to verify idempotency (should not duplicate)
        await seed_interview_modes()
        
        modes_after_second_seed = await repo.get_many({})
        assert len(modes_after_second_seed) == 4, "Idempotency failed: duplicated documents created."
    finally:
        await close_db()

