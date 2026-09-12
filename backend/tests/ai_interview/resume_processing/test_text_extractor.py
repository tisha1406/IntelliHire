import pytest
from app.ai_interview.resume_processing.text_extractor import TextExtractor
from app.ai_interview.resume_processing.schemas import ResumeFileInput
from app.ai_interview.resume_processing.exceptions import CorruptedFileError

def test_text_extractor_unsupported():
    from app.ai_interview.resume_processing.exceptions import UnsupportedFileTypeError
    file_input = ResumeFileInput(filename="resume.txt", content_type="text/plain", file_bytes=b"dummy")
    with pytest.raises(UnsupportedFileTypeError):
        TextExtractor.extract(file_input)

def test_text_extractor_corrupted_pdf():
    file_input = ResumeFileInput(filename="resume.pdf", content_type="application/pdf", file_bytes=b"not a real pdf")
    with pytest.raises(CorruptedFileError):
        TextExtractor.extract(file_input)

def test_text_extractor_corrupted_docx():
    file_input = ResumeFileInput(filename="resume.docx", content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document", file_bytes=b"not a real docx")
    with pytest.raises(CorruptedFileError):
        TextExtractor.extract(file_input)
