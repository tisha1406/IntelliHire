from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from the .env file.
    """

    # ==========================
    # MongoDB
    # ==========================
    MONGO_URI: str

    # ==========================
    # JWT
    # ==========================
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ==========================
    # AI API Keys
    # ==========================
    GROQ_API_KEY: str
    GEMINI_API_KEY: str
    SARVAM_API_KEY: str

    # ==========================
    # FastAPI
    # ==========================
    APP_NAME: str = "IntelliHire"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


@lru_cache
def get_settings() -> Settings:
    """
    Returns a cached instance of the application settings.
    """
    return Settings()


settings = get_settings()