import asyncio
# pyrefly: ignore [missing-import]
from motor.motor_asyncio import AsyncIOMotorClient

async def run_migration():
    client = AsyncIOMotorClient('mongodb://127.0.0.1:27017/intellihire')
    db = client.get_default_database()
    
    cursor = db.companies.find({})
    companies = await cursor.to_list(length=None)
    
    migrated_count = 0
    
    for company in companies:
        if "general" not in company:
            print(f"Migrating company {company.get('name', 'Unknown')} ({company['_id']})")
            
            new_doc = {
                "_id": company["_id"],
                "general": {
                    "name": company.get("name", "Unknown"),
                    "contact_email": company.get("contact_email", "unknown@example.com"),
                    "industry": company.get("industry", ""),
                    "website": company.get("website", ""),
                    "phone": company.get("phone", ""),
                    "logo_url": company.get("branding", {}).get("logo_url", "") if isinstance(company.get("branding"), dict) else ""
                },
                "subscription": {
                    "plan": company.get("subscription_plan", "Enterprise"),
                    "status": company.get("status", "active"),
                    "billing_cycle": "annual",
                    "seat_count": 5
                },
                "limits": {
                    "max_recruiters": company.get("max_recruiters", 5),
                    "max_candidates": company.get("max_candidates", 500),
                    "max_campaigns": company.get("max_campaigns", 10),
                    "monthly_interviews": company.get("monthly_interview_limit", 100),
                    "concurrent_interviews": 5,
                    "storage_limit_gb": company.get("storage_limit_gb", 10.0),
                    "api_requests_per_month": 10000,
                    "ai_credits": 1000,
                    "resume_uploads": company.get("resume_upload_limit", 5000)
                },
                "security": {
                    "login_enabled": True,
                    "mfa_required": False,
                    "password_policy": "standard",
                    "session_timeout_minutes": 60,
                    "jwt_lifetime_hours": 24,
                    "refresh_token_lifetime_days": 7,
                    "sso_enabled": False,
                    "allowed_domains": [],
                    "ip_whitelist": [],
                    "concurrent_sessions_allowed": 3,
                    "remember_me_allowed": True,
                    "login_attempts_before_lockout": 5
                },
                "features": {
                    "reports": company.get("reports_enabled", True),
                    "analytics": company.get("analytics_enabled", True),
                    "exports": company.get("exports_enabled", True),
                    "resume_screening": company.get("resume_screening_enabled", True),
                    "interview_analysis": company.get("interview_analysis_enabled", True),
                    "voice_interview": company.get("voice_interview_enabled", True),
                    "explainability": company.get("explainability_enabled", False),
                    "branding": company.get("branding_enabled", True),
                    "api_access": company.get("api_access_enabled", False),
                    "custom_questions": company.get("custom_questions_enabled", True)
                },
                "allowed_languages": company.get("allowed_languages", []),
                "allowed_voices": company.get("allowed_voices", []),
                "allowed_strategies": company.get("allowed_strategies", []),
                "allowed_interview_modes": company.get("allowed_interview_modes", []),
                "allowed_llm_tiers": company.get("allowed_llm_tiers", []),
                "created_at": company.get("created_at", "2026-01-01T00:00:00Z"),
                "updated_at": company.get("updated_at", "2026-01-01T00:00:00Z"),
                "deleted_at": company.get("deleted_at"),
                "created_by": company.get("created_by"),
                "deleted_by": company.get("deleted_by"),
                "credentials": company.get("credentials", {})
            }
            
            await db.companies.replace_one({"_id": company["_id"]}, new_doc)
            migrated_count += 1
            
    print(f"Migration completed. Migrated {migrated_count} old companies.")
    client.close()

if __name__ == "__main__":
    asyncio.run(run_migration())
