import io
import fitz  # PyMuPDF
from docx import Document

class ResumeParser:
    """
    Extracts raw text from PDF or DOCX files.
    """

    @staticmethod
    def extract_text(file_bytes: bytes, filename: str) -> str:
        ext = filename.split(".")[-1].lower()
        if ext == "pdf":
            return ResumeParser._extract_from_pdf(file_bytes)
        elif ext in ["doc", "docx"]:
            return ResumeParser._extract_from_docx(file_bytes)
        else:
            raise ValueError(f"Unsupported file format: {ext}")

    @staticmethod
    def _extract_from_pdf(file_bytes: bytes) -> str:
        text = ""
        try:
            # PyMuPDF
            doc = fitz.open(stream=file_bytes, filetype="pdf")
            for page in doc:
                text += page.get_text() + "\n"
        except Exception as e:
            # Fallback to pdfplumber could be added here if needed
            raise RuntimeError(f"Failed to parse PDF: {e}")
        return text

    @staticmethod
    def _extract_from_docx(file_bytes: bytes) -> str:
        text = ""
        try:
            doc = Document(io.BytesIO(file_bytes))
            for para in doc.paragraphs:
                text += para.text + "\n"
        except Exception as e:
            raise RuntimeError(f"Failed to parse DOCX: {e}")
        return text
