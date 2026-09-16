import io
import fitz  # PyMuPDF
import docx
from pydantic import BaseModel

class ParsedResume(BaseModel):
    text: str
    file_type: str
    page_count: int
    character_count: int

class ResumeParser:
    """
    Extracts raw text from PDF or DOCX files in memory.
    """

    @staticmethod
    def parse_file(file_bytes: bytes, filename: str) -> ParsedResume:
        if not file_bytes:
            raise ValueError("Resume file is required.")
            
        ext = filename.split(".")[-1].lower() if "." in filename else ""
        
        if ext == "pdf" or file_bytes.startswith(b"%PDF"):
            return ResumeParser.parse_pdf(file_bytes)
        elif ext in ["docx", "doc"] or file_bytes.startswith(b"PK\x03\x04"): # DOCX is a zip file
            if ext == "doc":
                raise ValueError("Unsupported resume format. Please upload a PDF or DOCX file.")
            return ResumeParser.parse_docx(file_bytes)
        else:
            raise ValueError("Unsupported resume format. Please upload a PDF or DOCX file.")

    @staticmethod
    def parse_pdf(file_bytes: bytes) -> ParsedResume:
        text = ""
        try:
            doc = fitz.open(stream=file_bytes, filetype="pdf")
            page_count = len(doc)
            for page in doc:
                page_text = page.get_text()
                if page_text:
                    text += page_text + "\n"
        except Exception as e:
            raise ValueError("The uploaded PDF could not be processed.")
        
        if not text.strip():
            raise ValueError("No readable text was found in the uploaded resume.")
            
        return ParsedResume(
            text=text,
            file_type="pdf",
            page_count=page_count,
            character_count=len(text)
        )

    @staticmethod
    def parse_docx(file_bytes: bytes) -> ParsedResume:
        text = ""
        try:
            doc = docx.Document(io.BytesIO(file_bytes))
            for para in doc.paragraphs:
                if para.text:
                    text += para.text + "\n"
            page_count = 1  # DOCX lacks reliable page count
        except Exception as e:
            raise ValueError("The uploaded DOCX could not be processed.")
            
        if not text.strip():
            raise ValueError("No readable text was found in the uploaded resume.")
            
        return ParsedResume(
            text=text,
            file_type="docx",
            page_count=page_count,
            character_count=len(text)
        )
