import asyncio

async def migrate_companies():
    from app.db.mongo import get_database, connect_db
    await connect_db()
    db = get_database()
    
    # We will grant all the new strategies to the test companies
    new_strategies = [
        "adaptive_depth",
        "fixed_coverage",
        "critical_skills_deep_dive",
        "breadth_screening",
        "requirement_gap_verification",
        "behavioral_adaptive"
    ]
    
    # Update companies that have legacy strategies
    result = await db.companies.update_many(
        {},
        {"$set": {"allowed_strategies": new_strategies}}
    )
    
    print(f"Migrated {result.modified_count} companies to new strategy entitlements.")

if __name__ == "__main__":
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    asyncio.run(migrate_companies())
