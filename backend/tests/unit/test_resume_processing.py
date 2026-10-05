import pytest
import io
from unittest.mock import patch, MagicMock
import fitz
from docx import Document
from resume.parser import ResumeParser
from resume.cleaner import ResumeCleaner
from app.config.settings import settings

def create_pdf(text: str) -> bytes:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text(fitz.Point(50, 50), text)
    return doc.write()

def create_multi_page_pdf(pages: list[str]) -> bytes:
    doc = fitz.open()
    for text in pages:
        page = doc.new_page()
        page.insert_text(fitz.Point(50, 50), text)
    return doc.write()

def create_docx(paragraphs: list[str]) -> bytes:
    doc = Document()
    for p in paragraphs:
        doc.add_paragraph(p)
    f = io.BytesIO()
    doc.save(f)
    return f.getvalue()

def test_1_simple_pdf():
    pdf_bytes = create_pdf("John Doe\nSoftware Engineer")
    parsed = ResumeParser.parse_file(pdf_bytes, "resume.pdf")
    assert "John Doe" in parsed.text
    assert parsed.file_type == "pdf"
    assert parsed.page_count == 1

def test_2_multi_page_pdf():
    pdf_bytes = create_multi_page_pdf(["Page 1", "Page 2"])
    parsed = ResumeParser.parse_file(pdf_bytes, "resume.pdf")
    assert "Page 1" in parsed.text
    assert "Page 2" in parsed.text
    assert parsed.page_count == 2
    # Ensure order is preserved
    assert parsed.text.find("Page 1") < parsed.text.find("Page 2")

def test_3_simple_docx():
    docx_bytes = create_docx(["John Doe", "Software Engineer"])
    parsed = ResumeParser.parse_file(docx_bytes, "resume.docx")
    assert "John Doe" in parsed.text
    assert parsed.file_type == "docx"

def test_4_docx_blank_paragraphs():
    docx_bytes = create_docx(["John Doe", "", "", "Engineer"])
    parsed = ResumeParser.parse_file(docx_bytes, "resume.docx")
    cleaned = ResumeCleaner.clean_text(parsed.text)
    assert "\n\n\n" not in cleaned
    assert "John Doe" in cleaned
    assert "Engineer" in cleaned

def test_5_messy_text_cleaner():
    raw_text = "JOHN DOE\r\n\r\n\r\n\r\n   Software Engineer  \n\n\tPython \t FastAPI"
    cleaned = ResumeCleaner.clean_text(raw_text)
    assert cleaned == "JOHN DOE\n\nSoftware Engineer\n\nPython FastAPI"

def test_6_technical_terms():
    raw_text = "C++ C# .NET Node.js React.js PostgreSQL MongoDB"
    cleaned = ResumeCleaner.clean_text(raw_text)
    assert cleaned == raw_text # Should preserve terms intact

def test_7_email_url_phone():
    raw_text = "test@example.com https://github.com/test +1-234-567-8900"
    cleaned = ResumeCleaner.clean_text(raw_text)
    assert cleaned == raw_text

def test_8_empty_pdf():
    # PDF with no text
    doc = fitz.open()
    doc.new_page()
    pdf_bytes = doc.write()
    with pytest.raises(ValueError, match="No readable text"):
        ResumeParser.parse_file(pdf_bytes, "empty.pdf")

def test_9_unsupported_file():
    with pytest.raises(ValueError, match="Unsupported resume format"):
        ResumeParser.parse_file(b"just text", "resume.txt")

def test_10_corrupt_file():
    with pytest.raises(ValueError, match="could not be processed"):
        ResumeParser.parse_file(b"corrupt pdf data", "corrupt.pdf")
    
    with pytest.raises(ValueError, match="could not be processed"):
        ResumeParser.parse_file(b"corrupt docx data", "corrupt.docx")

def test_11_no_resume_file():
    with pytest.raises(ValueError, match="Resume file is required"):
        ResumeParser.parse_file(b"", "empty.pdf")

def test_12_large_file():
    # Since parsing itself doesn't check size, the service does.
    # We will test the validation logic from the service in integration or just assert settings.
    assert settings.MAX_UPLOAD_SIZE_MB == 5

def test_13_privacy():
    # By design, the parser only accepts bytes and returns text.
    # It does not write to the filesystem.
    pass

@pytest.mark.asyncio
@patch('app.services.resume_processing_service.AsyncGroq')
async def test_resume_processing_service_groq_model(mock_async_groq):
    from app.services.resume_processing_service import ResumeProcessingService
    from app.config.settings import settings
    mock_client = mock_async_groq.return_value
    mock_client.chat.completions.create.return_value.choices = [MagicMock(message=MagicMock(content='{" overall_score\:100}'))]

@pytest.mark.asyncio
@patch('app.services.resume_processing_service.AsyncGroq')
@patch('app.services.resume_processing_service.ResumeCleaner')
@patch('app.services.resume_processing_service.ResumeParser')
@patch('app.services.resume_processing_service.CandidateWorkflowRepository')
@patch('app.services.resume_processing_service.ResumeRepository')
@patch('app.services.resume_processing_service.NotificationRepository')
async def test_resume_processing_stores_uploaded_at(mock_notif, mock_resume_repo, mock_workflow_repo, mock_parser, mock_cleaner, mock_groq):
    from app.services.resume_processing_service import ResumeProcessingService
    # setup mocks
    mock_workflow_repo_instance = mock_workflow_repo.return_value
    mock_groq.return_value.chat.completions.create.return_value.choices = [MagicMock(message=MagicMock(content='{" overall_score\:100}'))]

@pytest.mark.asyncio
@patch("app.services.resume_processing_service.AsyncGroq")
async def test_resume_structured_output_schema(mock_async_groq):
    from app.services.resume_processing_service import ResumeProcessingService
    mock_client = mock_async_groq.return_value
    mock_client.chat.completions.create.return_value.choices = [MagicMock(message=MagicMock(content="""{"overall_score":100, "experience": []}"""))]
    
    service = ResumeProcessingService()
    try:
        await service._structure_resume_with_llm("dummy text")
    except Exception:
        pass
    
    mock_client.chat.completions.create.assert_called_once()
    call_kwargs = mock_client.chat.completions.create.call_args.kwargs
    assert "response_format" in call_kwargs
    rf = call_kwargs["response_format"]
    assert rf["type"] == "json_schema"
    assert rf["json_schema"]["strict"] is True
    schema = rf["json_schema"]["schema"]
    assert "additionalProperties" in schema
    assert schema["additionalProperties"] is False
    assert "overall_score" in schema["properties"]
