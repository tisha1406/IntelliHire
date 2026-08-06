import logging
from app.db.mongo import get_database
from app.auth.jwt_handler import hash_password
from app.rbac.models import UserRole

logger = logging.getLogger("bootstrap")

async def bootstrap_platform():
    print("\n[BOOTSTRAP] Checking platform initialization...")
    
    db = get_database()
    
    # 1. System Administrator
    user_col = db.get_collection("users")
    admin_exists = await user_col.find_one({"role": UserRole.ADMIN.value})
    
    if admin_exists:
        print("[BOOTSTRAP] System Administrator exists.")
        print("[BOOTSTRAP] Initialization skipped.")
    else:
        print("[BOOTSTRAP] Admin not found.")
        print("[BOOTSTRAP] Creating System Administrator...")
        admin_doc = {
            "name": "System Administrator",
            "email": "admin@intellihire.dev",
            "password_hash": hash_password("admin123"),
            "role": UserRole.ADMIN.value,
            "status": "active"
        }
        await user_col.insert_one(admin_doc)

    # 2. Platform Settings
    settings_col = db.get_collection("platform_settings")
    settings_exists = await settings_col.find_one({"_id": "master_config"})
    
    if settings_exists:
        print("[BOOTSTRAP] Platform settings exist.")
    else:
        print("[BOOTSTRAP] Platform settings missing.")
        print("[BOOTSTRAP] Creating default platform configuration...")
        settings_doc = {
            "_id": "master_config",
            "general": {
                "platform_name": "IntelliHire",
                "support_email": "support@intellihire.dev",
                "max_companies": 500,
                "default_interview_duration": 30,
                "description": "IntelliHire — AI-Powered Interview Platform for modern recruiting teams."
            },
            "ai": {
                "primary_llm": "llama3",
                "stt_engine": "whisper",
                "max_questions": 12,
                "confidence_threshold": 75,
                "groq_api_key": "",
                "gemini_api_key": ""
            },
            "voices": {
                "en_us": True,
                "en_uk": False,
                "hi_in": True
            },
            "languages": {
                "english": True,
                "hindi": True,
                "spanish": False,
                "french": False
            },
            "modes": {
                "structured": True,
                "conversational": False,
                "technical": True,
                "behavioral": True,
                "campus": True
            },
            "strategies": {
                "default": True,
                "aggressive": False,
                "supportive": True,
                "exploratory": False
            },
            "notifications": {
                "email_alerts": True,
                "incident_alerts": True,
                "api_alerts": True,
                "weekly_digest": False
            },
            "security": {
                "mfa_required": False,
                "session_timeout": 30,
                "rate_limiting": True,
                "ip_whitelist": False
            },
            "appearance": {
                "theme": "dark",
                "accent": "blue",
                "compact_mode": False
            }
        }
        await settings_col.insert_one(settings_doc)

    # 3. RBAC Roles
    roles_col = db.get_collection("roles")
    role_count = await roles_col.count_documents({})
    
    if role_count > 0:
        print("[BOOTSTRAP] RBAC roles verified.")
    else:
        print("[BOOTSTRAP] Roles missing.")
        print("[BOOTSTRAP] Creating default RBAC roles...")
        roles = [
            {"name": "SUPER_ADMIN", "description": "Platform owner with unrestricted access."},
            {"name": "COMPANY_ADMIN", "description": "Tenant owner who manages company configuration and users."},
            {"name": "RECRUITER", "description": "User who can create campaigns and review candidates."},
            {"name": "INTERVIEWER", "description": "User who can only view specific candidates and conduct manual reviews."}
        ]
        await roles_col.insert_many(roles)

    # 4. Feature Definitions
    features_col = db.get_collection("feature_definitions")
    feature_count = await features_col.count_documents({})
    
    if feature_count > 0:
        print("[BOOTSTRAP] Feature definitions verified.")
    else:
        print("[BOOTSTRAP] Feature definitions missing.")
        print("[BOOTSTRAP] Creating master feature definitions...")
        features = [
            {"id": "reports", "name": "Reports & Analytics", "enabled": True, "category": "Analytics"},
            {"id": "analytics", "name": "Advanced Analytics", "enabled": True, "category": "Analytics"},
            {"id": "exports", "name": "Data Exports", "enabled": True, "category": "Data"},
            {"id": "resume_screening", "name": "Resume Screening", "enabled": True, "category": "Core"},
            {"id": "interview_analysis", "name": "Interview Analysis", "enabled": True, "category": "Core"},
            {"id": "voice_interview", "name": "Voice Interviews", "enabled": True, "category": "Core"},
            {"id": "explainability", "name": "Explainability Engine", "enabled": True, "category": "Advanced AI"},
            {"id": "branding", "name": "Custom Branding", "enabled": True, "category": "Customization"},
            {"id": "api_access", "name": "API Access", "enabled": False, "category": "Developer"},
            {"id": "custom_questions", "name": "Custom Questions", "enabled": True, "category": "Customization"},
            {"id": "anti_cheat", "name": "Anti-Cheat Systems", "enabled": True, "category": "Security"},
            {"id": "resume_parser", "name": "Resume Parser", "enabled": True, "category": "Core"},
            {"id": "cert_gen", "name": "Certificate Generation", "enabled": False, "category": "Customization"},
            {"id": "self_registration", "name": "Candidate Self Registration", "enabled": True, "category": "Core"}
        ]
        await features_col.insert_many(features)
        
    print("[BOOTSTRAP] Platform initialization complete.\n")
