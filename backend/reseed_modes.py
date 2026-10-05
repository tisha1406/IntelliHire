import asyncio
from app.db.mongo import connect_db, get_database, close_db
from scripts.seed_dev_data import seed_interview_modes

async def reseed_modes():
    await connect_db()
    db = get_database()
    
    print("Dropping old mode definitions...")
    await db["interview_mode_definitions"].delete_many({})
    
    print("Reseeding mode definitions...")
    await seed_interview_modes()
    
    # Verify
    modes = await db["interview_mode_definitions"].find({}).to_list(100)
    for mode in modes:
        print(f"Mode: {mode['mode_id']} -> {mode['settings']['allowed_question_types']}")
        
    await close_db()

if __name__ == "__main__":
    asyncio.run(reseed_modes())
