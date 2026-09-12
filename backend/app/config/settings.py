from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    IntelliHire application settings.
    Loaded automatically from the .env file.
    IntelliHire application settings loaded from the .env file.
    """

    # ==========================================================
    # MongoDB
    # ==========================================================
    MONGO_URI: str
    DATABASE_NAME: str = "intellihire"

    # ==========================================================
    # JWT
    # ==========================================================
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ==========================================================
    # AI Providers
    # AI API Keys
    # ==========================================================
    GROQ_API_KEY: str
    GEMINI_API_KEY: str
    SARVAM_API_KEY: str
    
    # ==========================================================
    # Speech Infrastructure (Phase 11.5)
    # ==========================================================
    SPEECH_STT_PROVIDER: str = "sarvam"
    SPEECH_TTS_PROVIDER: str = "sarvam"
    
    SARVAM_STT_MODEL: str = "saaras:v1"
    SARVAM_TTS_MODEL: str = "bulbul:v1"
    
    STT_MAX_ATTEMPTS: int = 3
    STT_MAX_OPERATION_TIME_SECONDS: int = 60
    
    TTS_MAX_ATTEMPTS: int = 3
    TTS_MAX_OPERATION_TIME_SECONDS: int = 60

    # ==========================================================
    # FastAPI
    # ==========================================================
    APP_NAME: str = "IntelliHire"
    APP_VERSION: str = "1.0.0"

    DEBUG: bool = True

    # ==========================================================
    # Phase 9 — Interview Transport
    # ==========================================================
    # Max worker threads for running synchronous engine operations
    # (LLM calls may take up to 30s; keep bounded to avoid thread exhaustion)
    INTERVIEW_EXECUTOR_MAX_WORKERS: int = 10

    # Maximum answer text length in characters (transport-level guard)
    MAX_ANSWER_TEXT_CHARS: int = 8000

    # Maximum raw WebSocket message size in bytes
    MAX_WS_MESSAGE_BYTES: int = 32_768  # 32 KB

    # Evaluation lease duration in seconds (re-claimable after expiry)
    EVALUATION_LEASE_SECONDS: int = 90

    # Question generation lease duration in seconds
    GENERATION_LEASE_SECONDS: int = 60

    # ==========================================================
    # Environment
    # ==========================================================
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """
    Return cached application settings.
    """
    return Settings()


settings = get_settings()