import pytest
from app.ai_interview.core.enums import QuestionType
from app.db.mongo import get_database
from scripts.seed_dev_data import seed_interview_modes

@pytest.mark.asyncio
async def test_seeded_modes_use_canonical_question_types():
    """
    Focused test to ensure the seed data only uses valid QuestionTypes.
    Prevents the ValueError: 'technical_deep_dive' is not a valid QuestionType crash.
    """
    # Seed data into the test database (using isolation)
    from app.db.mongo import connect_db, close_db
    await connect_db()
    try:
        await seed_interview_modes()
        
        db = get_database()
        modes = await db["interview_mode_definitions"].find({}).to_list(100)
        assert len(modes) > 0, "Modes should be seeded"
        
        valid_types = {qt.value for qt in QuestionType}
        
        for mode in modes:
            allowed = mode.get("settings", {}).get("allowed_question_types", [])
            for qt_str in allowed:
                assert qt_str in valid_types, (
                    f"Mode '{mode.get('mode_id')}' uses invalid QuestionType: '{qt_str}'. "
                    f"Must be one of {valid_types}."
                )
                assert qt_str != "technical_deep_dive"
    finally:
        await close_db()
