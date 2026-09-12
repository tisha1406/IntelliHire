import pytest
from app.ai_interview.resume_processing.file_validator import FileValidator
from app.ai_interview.resume_processing.schemas import ResumeFileInput
from app.ai_interview.resume_processing.exceptions import (
    UnsupportedFileTypeError,
    FileTooLargeError,
    EmptyFileError,
)
from app.ai_interview.resume_processing.config import ResumeProcessingConfig

def test_file_validator_valid_pdf():
    file_input = ResumeFileInput(filename="resume.pdf", content_type="application/pdf", file_bytes=b"dummy content")
    # Should not raise
    FileValidator.validate(file_input)

def test_file_validator_valid_docx():
    file_input = ResumeFileInput(filename="resume.docx", content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document", file_bytes=b"dummy content")
    FileValidator.validate(file_input)

def test_file_validator_unsupported_extension():
    file_input = ResumeFileInput(filename="resume.txt", content_type="text/plain", file_bytes=b"dummy content")
    with pytest.raises(UnsupportedFileTypeError):
        FileValidator.validate(file_input)

def test_file_validator_empty_file():
    file_input = ResumeFileInput(filename="resume.pdf", content_type="application/pdf", file_bytes=b"")
    with pytest.raises(EmptyFileError):
        FileValidator.validate(file_input)

def test_file_validator_oversized_file():
    huge_bytes = b"0" * (ResumeProcessingConfig.MAX_RESUME_FILE_SIZE_BYTES + 1)
    file_input = ResumeFileInput(filename="resume.pdf", content_type="application/pdf", file_bytes=huge_bytes)
    with pytest.raises(FileTooLargeError):
        FileValidator.validate(file_input)
