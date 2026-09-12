import os
from app.ai_interview.resume_processing.schemas import ResumeFileInput
from app.ai_interview.resume_processing.exceptions import (
    UnsupportedFileTypeError,
    FileTooLargeError,
    EmptyFileError,
)
from app.ai_interview.resume_processing.config import ResumeProcessingConfig

class FileValidator:
    ALLOWED_EXTENSIONS = {".pdf", ".docx", ".doc"}
    ALLOWED_MIME_TYPES = {
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/msword"
    }

    @staticmethod
    def validate(file_input: ResumeFileInput) -> None:
        if not file_input.file_bytes:
            raise EmptyFileError("File is empty.")

        if len(file_input.file_bytes) > ResumeProcessingConfig.MAX_RESUME_FILE_SIZE_BYTES:
            raise FileTooLargeError(f"File size exceeds the {ResumeProcessingConfig.MAX_RESUME_FILE_SIZE_BYTES} bytes limit.")

        ext = os.path.splitext(file_input.filename)[1].lower()
        if ext not in FileValidator.ALLOWED_EXTENSIONS:
            raise UnsupportedFileTypeError(f"Unsupported file extension: {ext}. Allowed: {FileValidator.ALLOWED_EXTENSIONS}")

        # Note: Actual readability parsing is deferred to TextExtractor as requested by the user.
