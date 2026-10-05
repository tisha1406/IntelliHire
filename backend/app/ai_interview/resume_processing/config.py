from app.config.settings import settings

class ResumeProcessingConfig:
    MAX_RESUME_FILE_SIZE_BYTES = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    MIN_EXTRACTED_TEXT_CHARACTERS = 100
