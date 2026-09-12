from typing import Optional, List, Dict
from pydantic import BaseModel, Field
from datetime import datetime, timezone
from app.ai_interview.resume_processing.enums import ExtractionQualityStatus, ExtractionWarningCode
from app.ai_interview.schemas.resume import StructuredResume

class ResumeFileInput(BaseModel):
    filename: str
    content_type: str
    file_bytes: bytes

class ResumeProcessingRequest(BaseModel):
    resume_file: ResumeFileInput
    candidate_id: Optional[str] = None

class ExtractedDocument(BaseModel):
    raw_text: str
    page_count: int
    character_count: int
    source_type: str

class NormalizedResumeText(BaseModel):
    sections: Dict[str, str] = Field(default_factory=dict)
    unclassified_text: str = ""

class ExtractionWarning(BaseModel):
    code: ExtractionWarningCode
    message: str
    stage: str

class ExtractionMetadata(BaseModel):
    source_type: str
    extractor_name: str
    extractor_version: str
    character_count: int
    detected_sections: List[str]
    warning_count: int
    processing_duration_ms: float

class CandidateInterviewContext(BaseModel):
    candidate_id: Optional[str]
    structured_resume: StructuredResume
    extraction_metadata: ExtractionMetadata
    quality_status: ExtractionQualityStatus
    warnings: List[ExtractionWarning] = Field(default_factory=list)
