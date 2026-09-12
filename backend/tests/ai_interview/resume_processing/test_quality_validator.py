import pytest
from app.ai_interview.resume_processing.quality_validator import QualityValidator
from app.ai_interview.resume_processing.schemas import ExtractedDocument, NormalizedResumeText
from app.ai_interview.resume_processing.enums import ExtractionQualityStatus, ExtractionWarningCode
from app.ai_interview.resume_processing.exceptions import ExtractionFailedError
from app.ai_interview.resume_processing.config import ResumeProcessingConfig

def test_quality_validator_zero_text():
    doc = ExtractedDocument(raw_text="", page_count=1, character_count=0, source_type="pdf")
    norm = NormalizedResumeText()
    with pytest.raises(ExtractionFailedError):
        QualityValidator.validate(doc, norm)

def test_quality_validator_low_text():
    doc = ExtractedDocument(raw_text="short", page_count=1, character_count=5, source_type="pdf")
    norm = NormalizedResumeText(sections={"education": "...", "experience": "...", "skills": "..."})
    status, warnings = QualityValidator.validate(doc, norm)
    
    assert status == ExtractionQualityStatus.PARTIALLY_USABLE
    assert any(w.code == ExtractionWarningCode.LOW_TEXT_CONTENT for w in warnings)

def test_quality_validator_missing_sections():
    doc = ExtractedDocument(raw_text="A" * ResumeProcessingConfig.MIN_EXTRACTED_TEXT_CHARACTERS, page_count=1, character_count=ResumeProcessingConfig.MIN_EXTRACTED_TEXT_CHARACTERS, source_type="pdf")
    norm = NormalizedResumeText(sections={}) # No ed, exp, skills
    status, warnings = QualityValidator.validate(doc, norm)
    
    assert status == ExtractionQualityStatus.PARTIALLY_USABLE
    assert len(warnings) == 3
    assert any(w.code == ExtractionWarningCode.NO_EDUCATION_DETECTED for w in warnings)
    assert any(w.code == ExtractionWarningCode.NO_EXPERIENCE_DETECTED for w in warnings)
    assert any(w.code == ExtractionWarningCode.NO_SKILLS_DETECTED for w in warnings)

def test_quality_validator_usable():
    doc = ExtractedDocument(raw_text="A" * ResumeProcessingConfig.MIN_EXTRACTED_TEXT_CHARACTERS, page_count=1, character_count=ResumeProcessingConfig.MIN_EXTRACTED_TEXT_CHARACTERS, source_type="pdf")
    norm = NormalizedResumeText(sections={"education": "...", "experience": "...", "skills": "..."})
    status, warnings = QualityValidator.validate(doc, norm)
    
    assert status == ExtractionQualityStatus.USABLE
    assert len(warnings) == 0
