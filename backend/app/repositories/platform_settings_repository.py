from app.repositories.base_repository import BaseRepository

class PlatformSettingsRepository(BaseRepository):
    def __init__(self):
        super().__init__("platform_settings")

    async def get_settings(self):
        # We only ever have ONE settings document. We identify it by a constant id or just take the first.
        settings = await self.collection.find_one({"_id": "master_config"})
        if not settings:
            # Initialize default if it doesn't exist
            settings = {
                "_id": "master_config",
                "general": {
                    "platform_name": "IntelliHire",
                    "support_email": "support@intellihire.com",
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
            await self.collection.insert_one(settings)
        return settings

    async def update_settings(self, payload: dict):
        result = await self.collection.update_one(
            {"_id": "master_config"},
            {"$set": payload},
            upsert=True
        )
        return result.modified_count > 0 or result.upserted_id is not None

    async def get_master_config(self):
        config = await self.get_one({"type": "master_config"})
        if not config:
            # Seed default config if none exists
            config = {
                "type": "master_config",
                "ai_models": [
                    {"id": "gemini", "name": "Gemini 1.5 Pro", "provider": "Google", "enabled": True},
                    {"id": "groq", "name": "Groq Llama 3", "provider": "Groq", "enabled": True},
                    {"id": "claude", "name": "Claude 3.5 Sonnet", "provider": "Anthropic", "enabled": False},
                    {"id": "gpt4", "name": "GPT-4o", "provider": "OpenAI", "enabled": False}
                ],
                "features": [
                    {"id": "reports", "name": "Reports & Analytics", "enabled": True, "category": "Analytics"},
                    {"id": "analytics", "name": "Advanced Analytics", "enabled": True, "category": "Analytics"},
                    {"id": "exports", "name": "Data Exports", "enabled": True, "category": "Data"},
                    {"id": "resume_screening", "name": "Resume Screening", "enabled": True, "category": "Core"},
                    {"id": "interview_analysis", "name": "Interview Analysis", "enabled": True, "category": "Core"},
                    {"id": "voice_interview", "name": "Voice Interviews", "enabled": True, "category": "Core"},
                    {"id": "explainability", "name": "Explainability Engine", "enabled": True, "category": "Advanced AI"},
                    {"id": "branding", "name": "Custom Branding", "enabled": True, "category": "Customization"},
                    {"id": "api_access", "name": "API Access", "enabled": False, "category": "Developer"},
                    {"id": "custom_questions", "name": "Custom Questions", "enabled": True, "category": "Customization"}
                ],
                "security_policies": {
                    "mfa_required": False,
                    "password_expiration_days": 90,
                    "session_timeout_minutes": 60
                }
            }
            await self.create(config)
            config = await self.get_one({"type": "master_config"})
        return config
