import pytest
from unittest.mock import patch, MagicMock
from app.ai_interview.resume_processing.pipeline import ResumeProcessingPipeline
from app.ai_interview.resume_processing.schemas import (
    ResumeProcessingRequest, 
    ResumeFileInput,
    ExtractedDocument,
    NormalizedResumeText
)
from app.ai_interview.resume_processing.enums import ExtractionQualityStatus
from app.ai_interview.schemas.resume import StructuredResume

@patch('app.ai_interview.resume_processing.pipeline.FileValidator.validate')
@patch('app.ai_interview.resume_processing.pipeline.TextExtractor.extract')
def test_pipeline_student_heavy_resume(mock_extract, mock_validate):
    mock_extract.return_value = ExtractedDocument(
        raw_text="Education:\nUniversity A\nProjects:\nProject X\nProject Y\nSkills:\nPython",
        page_count=1,
        character_count=100,
        source_type="pdf"
    )
    pipeline = ResumeProcessingPipeline()
    req = ResumeProcessingRequest(
        resume_file=ResumeFileInput(filename="resume.pdf", content_type="application/pdf", file_bytes=b"dummy"),
    )
    context = pipeline.process(req)
    # Valid output even without experience
    assert context.quality_status == ExtractionQualityStatus.PARTIALLY_USABLE # Missing experience
    assert len(context.structured_resume.education) == 1
    assert len(context.structured_resume.projects) == 2
    assert len(context.structured_resume.experience) == 0

@patch('app.ai_interview.resume_processing.pipeline.FileValidator.validate')
@patch('app.ai_interview.resume_processing.pipeline.TextExtractor.extract')
def test_pipeline_experienced_resume(mock_extract, mock_validate):
    mock_extract.return_value = ExtractedDocument(
        raw_text="Experience:\nRole A\nRole B\nSkills:\nJava",
        page_count=2,
        character_count=150,
        source_type="pdf"
    )
    pipeline = ResumeProcessingPipeline()
    req = ResumeProcessingRequest(
        resume_file=ResumeFileInput(filename="resume.pdf", content_type="application/pdf", file_bytes=b"dummy"),
    )
    context = pipeline.process(req)
    assert context.quality_status == ExtractionQualityStatus.PARTIALLY_USABLE # Missing education
    assert len(context.structured_resume.experience) == 2
    assert len(context.structured_resume.projects) == 0

@patch('app.ai_interview.resume_processing.pipeline.FileValidator.validate')
@patch('app.ai_interview.resume_processing.pipeline.TextExtractor.extract')
def test_pipeline_short_legitimate(mock_extract, mock_validate):
    # Short but legitimate (has one section but few characters)
    mock_extract.return_value = ExtractedDocument(
        raw_text="Experience:\nRole A",
        page_count=1,
        character_count=20, # Very short
        source_type="pdf"
    )
    pipeline = ResumeProcessingPipeline()
    req = ResumeProcessingRequest(
        resume_file=ResumeFileInput(filename="resume.pdf", content_type="application/pdf", file_bytes=b"dummy"),
    )
    context = pipeline.process(req)
    assert context.quality_status == ExtractionQualityStatus.PARTIALLY_USABLE

@patch('app.ai_interview.resume_processing.pipeline.FileValidator.validate')
@patch('app.ai_interview.resume_processing.pipeline.TextExtractor.extract')
def test_pipeline_unusable(mock_extract, mock_validate):
    # Extremely short and no sections
    mock_extract.return_value = ExtractedDocument(
        raw_text="hello world",
        page_count=1,
        character_count=11,
        source_type="pdf"
    )
    pipeline = ResumeProcessingPipeline()
    req = ResumeProcessingRequest(
        resume_file=ResumeFileInput(filename="resume.pdf", content_type="application/pdf", file_bytes=b"dummy"),
    )
    from app.ai_interview.resume_processing.exceptions import ExtractionFailedError
    with pytest.raises(ExtractionFailedError, match="UNUSABLE"):
        pipeline.process(req)
