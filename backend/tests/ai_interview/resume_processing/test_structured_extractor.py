from app.ai_interview.resume_processing.structured_extractor import DeterministicResumeStructuredExtractor
from app.ai_interview.resume_processing.schemas import NormalizedResumeText

def test_deterministic_structured_extractor():
    extractor = DeterministicResumeStructuredExtractor()
    normalized = NormalizedResumeText(
        sections={
            "summary": "Summary text",
            "education": "University A\nUniversity B",
            "experience": "Role A\nRole B",
            "skills": "Python, Java\nC++"
        },
        unclassified_text="John Doe"
    )
    
    resume = extractor.extract(normalized)
    
    assert resume.professional_summary == "Summary text"
    assert len(resume.education) == 2
    assert resume.education[0].degree == "University A"
    assert len(resume.experience) == 2
    assert resume.experience[0].title == "Role A"
    assert len(resume.skills) == 3
    assert resume.skills[0].name == "Python"
