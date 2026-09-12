import pytest
from app.ai_interview.transport.services.mode_resolver import resolve_interview_mode

def test_resolve_interview_mode_legacy():
    campaign = {
        "interview_mode": "structured"
    }
    assert resolve_interview_mode(campaign) == "structured"

def test_resolve_interview_mode_current():
    campaign = {
        "interview_settings": {
            "type": "Technical"
        }
    }
    assert resolve_interview_mode(campaign) == "technical"

def test_resolve_interview_mode_complex_string():
    campaign = {
        "interview_settings": {
            "type": "AI & Data Science"
        }
    }
    assert resolve_interview_mode(campaign) == "ai_&_data_science"

def test_resolve_interview_mode_missing():
    campaign = {}
    with pytest.raises(ValueError, match="missing both 'interview_mode' and 'interview_settings.type'"):
        resolve_interview_mode(campaign)

def test_resolve_interview_mode_empty_settings():
    campaign = {
        "interview_settings": {}
    }
    with pytest.raises(ValueError, match="missing both 'interview_mode' and 'interview_settings.type'"):
        resolve_interview_mode(campaign)

def test_resolve_interview_mode_empty_string():
    campaign = {
        "interview_mode": "   "
    }
    with pytest.raises(ValueError, match="missing both 'interview_mode' and 'interview_settings.type'"):
        resolve_interview_mode(campaign)

def test_resolve_interview_mode_prioritizes_legacy_if_both_exist():
    campaign = {
        "interview_mode": "legacy_mode",
        "interview_settings": {
            "type": "new_mode"
        }
    }
    # Should prioritize the top level if it exists for some reason
    assert resolve_interview_mode(campaign) == "legacy_mode"
