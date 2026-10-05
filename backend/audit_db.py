import asyncio
import json
from bson import ObjectId

class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        if hasattr(o, "isoformat"):
            return o.isoformat()
        return super().default(o)

async def audit_db():
    from app.db.mongo import get_database, connect_db
    await connect_db()
    db = get_database()
    
    strategies = await db.strategies.find({}).to_list(length=None)
    
    companies = await db.companies.find({}).to_list(length=10)
    
    output = {
        "strategies": strategies,
        "companies": [
            {
                "id": str(c.get("_id")),
                "name": c.get("name"),
                "email": c.get("email"),
                "allowed_strategies": c.get("allowed_strategies"),
                "subscription_tier": c.get("subscription_tier")
            } for c in companies
        ]
    }
    
    with open("audit_results.json", "w") as f:
        json.dump(output, f, cls=JSONEncoder, indent=2)

if __name__ == "__main__":
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    asyncio.run(audit_db())
