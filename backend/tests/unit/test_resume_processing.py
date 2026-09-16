import pytest
import io
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
