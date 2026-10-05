from typing import Dict, Any
import pytest
from app.ai_interview.transport.services.resume_context_bridge import ResumeContextBridge
from app.ai_interview.resume_processing.enums import ExtractionQualityStatus

def test_resume_context_bridge_quality_status():
    """
    Focused regression test to verify that ResumeContextBridge.build()
    assigns ExtractionQualityStatus.USABLE to the candidate_context,
    avoiding the previous AttributeError: HIGH mismatch.
    """
    resume_doc: Dict[str, Any] = {
        "extracted_data": {
            "professional_summary": "Experienced Python Developer.",
            "education": [{"degree": "B.Sc.", "institution": "Tech University", "year": "2020"}],
            "experience": [{"title": "Software Engineer", "org": "Tech Corp", "description": "Developed things."}],
            "skills": ["Python", "FastAPI"],
            "projects": [],
            "certifications": []
        }
    }
    candidate_id = "test_candidate_id"

    # Should build without raising AttributeError
    context = ResumeContextBridge.build(resume_doc, candidate_id)

    assert context.candidate_id == candidate_id
    assert context.quality_status == ExtractionQualityStatus.USABLE
    assert context.structured_resume.professional_summary == "Experienced Python Developer."
