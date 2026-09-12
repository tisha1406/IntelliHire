from app.ai_interview.resume_processing.text_cleaner import TextCleaner

def test_text_cleaner_whitespace_normalization():
    raw_text = "Software    Engineer\n\n\n\nABC Company\n\n2024"
    cleaned = TextCleaner.clean(raw_text)
    assert "Software Engineer" in cleaned
    assert "ABC Company" in cleaned
    assert "\n\n\n" not in cleaned # Max 2 newlines

def test_text_cleaner_page_number_cleanup():
    raw_text = "Page 1 of 2\nExperience\nPage 2 of 2"
    cleaned = TextCleaner.clean(raw_text)
    assert "Page 1 of 2" not in cleaned
    assert "Page 2 of 2" not in cleaned
    assert "Experience" in cleaned
