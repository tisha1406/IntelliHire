from app.ai_interview.resume_processing.resume_normalizer import ResumeNormalizer

def test_resume_normalizer_section_detection():
    cleaned_text = "Professional Summary\nGreat dev\nExperience:\nCompany A\nEducation\nUniversity B"
    normalized = ResumeNormalizer.normalize(cleaned_text)
    
    assert "summary" in normalized.sections
    assert "Great dev" in normalized.sections["summary"]
    
    assert "experience" in normalized.sections
    assert "Company A" in normalized.sections["experience"]
    
    assert "education" in normalized.sections
    assert "University B" in normalized.sections["education"]

def test_resume_normalizer_unclassified_text():
    cleaned_text = "John Doe\njohn@doe.com\nExperience:\nCompany A"
    normalized = ResumeNormalizer.normalize(cleaned_text)
    
    assert "John Doe" in normalized.unclassified_text
    assert "john@doe.com" in normalized.unclassified_text
    assert "Company A" in normalized.sections["experience"]
