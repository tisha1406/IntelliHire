import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient

from app.main import app
from app.auth.jwt_handler import create_access_token
from app.ai_interview.core.enums import InterviewType
import uuid
from bson import ObjectId



@pytest.fixture
def client():
    with TestClient(app) as client:
        yield client

@pytest.fixture
def company_token() -> str:
    uid = str(ObjectId())
    return create_access_token(
        user_id=uid,
        role="company",
        company_id=uid
    )

def get_base_campaign_payload():
    return {
        "name": "Test Campaign",
        "department": "Engineering",
        "location": "Remote",
        "deadline": "2026-12-31",
        "salary": "100k",
        "description": "Test description",
        "employment_type": "full_time",
        "requirements": [{"skill": "Python", "criticality": "required"}],
        "interview_settings": {
            "duration": 30,
            "strictness": "medium",
            "type": "technical"
        }
    }

@patch("app.api.company.campaigns.CompanyRepository")
@patch("app.middleware.limits.CompanyRepository")
@patch("app.api.company.campaigns.StrategyRepository")
@patch("app.api.company.campaigns.CampaignRepository")
def test_campaign_create_valid_strategy(mock_camp_repo, mock_strat_repo, mock_limits_comp_repo, mock_comp_repo, client, company_token):
    headers = {"Authorization": f"Bearer {company_token}"}
    
    # Mock company doc
    mock_comp_instance = AsyncMock()
    mock_comp_instance.get_by_id.return_value = {
        "_id": str(ObjectId()),
        "status": "active",
        "subscription": {"status": "active"},
        "limits": {"max_campaigns": 10},
        "usage": {"campaigns_used": 0},
        # Real company documents store strategy display NAMES in
        # allowed_strategies (set via CompanyWizard/StrategiesTab.jsx's
        # `strat.name`), not strategy_id slugs.
        "allowed_strategies": ["Test Strat"]
    }
    mock_comp_repo.return_value = mock_comp_instance
    mock_limits_comp_repo.return_value = mock_comp_instance

    # Mock strategy doc
    mock_strat_instance = AsyncMock()
    mock_strat_instance.get_latest_version.return_value = {
        "strategy_id": "test_strat_1",
        "name": "Test Strat",
        "description": "desc",
        "version": 1,
        "is_active": True,
        "applicable_interview_types": ["technical"],
        "min_questions": 5,
        "target_questions": 10,
        "max_questions": 15,
        "max_questions_per_topic": 3,
        "max_followups_per_topic": 2,
        "strong_threshold": 0.8,
        "acceptable_threshold": 0.6,
        "weak_threshold": 0.4,
        "topic_selection_policy": {},
        "difficulty_policy": {},
        "followup_policy": {},
        "gap_policy": {},
        "completion_policy": {},
        "company_override_bounds": {
            "target_questions_min_delta": -2,
            "target_questions_max_delta": 2,
            "allowed_difficulty_bands": ["medium", "hard"]
        }
    }
    mock_strat_repo.return_value = mock_strat_instance
    
    mock_camp_instance = AsyncMock()
    mock_camp_instance.create.return_value = str(uuid.uuid4())
    mock_camp_repo.return_value = mock_camp_instance
    
    payload = get_base_campaign_payload()
    payload["strategy_id"] = "test_strat_1"
    payload["interview_type"] = "technical"
    
    resp = client.post("/company/campaigns/", json=payload, headers=headers)
    assert resp.status_code == 201, resp.json()

@patch("app.api.company.campaigns.CompanyRepository")
@patch("app.middleware.limits.CompanyRepository")
@patch("app.api.company.campaigns.StrategyRepository")
@patch("app.api.company.campaigns.CampaignRepository")
def test_campaign_create_invalid_mixed_composition(mock_camp_repo, mock_strat_repo, mock_limits_comp_repo, mock_comp_repo, client, company_token):
    headers = {"Authorization": f"Bearer {company_token}"}
    
    mock_comp_instance = AsyncMock()
    mock_comp_instance.get_by_id.return_value = {
        "_id": str(ObjectId()),
        "status": "active",
        "subscription": {"status": "active"},
        "limits": {"max_campaigns": 10},
        "usage": {"campaigns_used": 0},
        "allowed_strategies": ["mixed_strat"]
    }
    mock_comp_repo.return_value = mock_comp_instance
    mock_limits_comp_repo.return_value = mock_comp_instance
    
    mock_strat_instance = AsyncMock()
    mock_strat_instance.get_latest_version.return_value = {
        "strategy_id": "mixed_strat",
        "name": "Mixed Strat",
        "description": "desc",
        "version": 1,
        "is_active": True,
        "applicable_interview_types": ["mixed"],
        "min_questions": 5,
        "target_questions": 10,
        "max_questions": 15,
        "max_questions_per_topic": 3,
        "max_followups_per_topic": 2,
        "strong_threshold": 0.8,
        "acceptable_threshold": 0.6,
        "weak_threshold": 0.4,
        "topic_selection_policy": {},
        "difficulty_policy": {},
        "followup_policy": {},
        "gap_policy": {},
        "completion_policy": {},
        "company_override_bounds": {}
    }
    mock_strat_repo.return_value = mock_strat_instance
    
    payload = get_base_campaign_payload()
    payload["strategy_id"] = "mixed_strat"
    payload["interview_type"] = "mixed"
    
    # Below 10%
    payload["mixed_composition"] = {
        "technical": 0.95,
        "resume_experience": 0.05,
        "hr_behavioral": 0,
        "situational_case": 0
    }
    resp = client.post("/company/campaigns/", json=payload, headers=headers)
    assert resp.status_code == 422
    assert "minimum weight of 0.10" in str(resp.json()).lower()


@patch("app.api.company.campaigns.CompanyRepository")
@patch("app.middleware.limits.CompanyRepository")
@patch("app.api.company.campaigns.StrategyRepository")
@patch("app.api.company.campaigns.CampaignRepository")
def test_campaign_create_strategy_not_allowed(mock_camp_repo, mock_strat_repo, mock_limits_comp_repo, mock_comp_repo, client, company_token):
    headers = {"Authorization": f"Bearer {company_token}"}
    
    mock_comp_instance = AsyncMock()
    mock_comp_instance.get_by_id.return_value = {
        "_id": str(ObjectId()),
        "status": "active",
        "subscription": {"status": "active"},
        "limits": {"max_campaigns": 10},
        "usage": {"campaigns_used": 0},
        # Real company documents list allowed strategies by display NAME.
        "allowed_strategies": ["Allowed Strategy"]
    }
    mock_comp_repo.return_value = mock_comp_instance
    mock_limits_comp_repo.return_value = mock_comp_instance

    # The strategy must actually exist/be active for its own (disallowed)
    # name to be compared against allowed_strategies.
    mock_strat_instance = AsyncMock()
    mock_strat_instance.get_latest_version.return_value = {
        "strategy_id": "disallowed_strat",
        "name": "Disallowed Strategy",
        "is_active": True,
    }
    mock_strat_repo.return_value = mock_strat_instance

    payload = get_base_campaign_payload()
    payload["strategy_id"] = "disallowed_strat"

    resp = client.post("/company/campaigns/", json=payload, headers=headers)
    assert resp.status_code == 403
    assert "strategy not allowed" in str(resp.json()).lower()


@patch("app.api.company.campaigns.CompanyRepository")
@patch("app.middleware.limits.CompanyRepository")
@patch("app.api.company.campaigns.StrategyRepository")
@patch("app.api.company.campaigns.CampaignRepository")
def test_campaign_create_unknown_strategy(mock_camp_repo, mock_strat_repo, mock_limits_comp_repo, mock_comp_repo, client, company_token):
    headers = {"Authorization": f"Bearer {company_token}"}
    
    mock_comp_instance = AsyncMock()
    mock_comp_instance.get_by_id.return_value = {
        "_id": str(ObjectId()),
        "status": "active",
        "subscription": {"status": "active"},
        "limits": {"max_campaigns": 10},
        "usage": {"campaigns_used": 0},
        "allowed_strategies": ["unknown_strat"]
    }
    mock_comp_repo.return_value = mock_comp_instance
    mock_limits_comp_repo.return_value = mock_comp_instance
    
    mock_strat_instance = AsyncMock()
    mock_strat_instance.get_latest_version.return_value = None
    mock_strat_repo.return_value = mock_strat_instance
    
    payload = get_base_campaign_payload()
    payload["strategy_id"] = "unknown_strat"
    
    resp = client.post("/company/campaigns/", json=payload, headers=headers)
    assert resp.status_code == 404
    assert "not found" in str(resp.json()).lower()


@patch("app.api.company.campaigns.CompanyRepository")
@patch("app.middleware.limits.CompanyRepository")
@patch("app.api.company.campaigns.StrategyRepository")
@patch("app.api.company.campaigns.CampaignRepository")
def test_campaign_create_incompatible_interview_type(mock_camp_repo, mock_strat_repo, mock_limits_comp_repo, mock_comp_repo, client, company_token):
    headers = {"Authorization": f"Bearer {company_token}"}
    
    mock_comp_instance = AsyncMock()
    mock_comp_instance.get_by_id.return_value = {
        "_id": str(ObjectId()),
        "status": "active",
        "subscription": {"status": "active"},
        "limits": {"max_campaigns": 10},
        "usage": {"campaigns_used": 0},
        "allowed_strategies": ["Test Strat"]
    }
    mock_comp_repo.return_value = mock_comp_instance
    mock_limits_comp_repo.return_value = mock_comp_instance

    mock_strat_instance = AsyncMock()
    mock_strat_instance.get_latest_version.return_value = {
        "strategy_id": "test_strat_1",
        "name": "Test Strat",
        "description": "desc",
        "version": 1,
        "is_active": True,
        "applicable_interview_types": ["technical"],
        "min_questions": 5,
        "target_questions": 10,
        "max_questions": 15,
        "max_questions_per_topic": 3,
        "max_followups_per_topic": 2,
        "strong_threshold": 0.8,
        "acceptable_threshold": 0.6,
        "weak_threshold": 0.4,
        "topic_selection_policy": {},
        "difficulty_policy": {},
        "followup_policy": {},
        "gap_policy": {},
        "completion_policy": {},
        "company_override_bounds": {}
    }
    mock_strat_repo.return_value = mock_strat_instance

    payload = get_base_campaign_payload()
    payload["strategy_id"] = "test_strat_1"
    payload["interview_type"] = "hr_behavioral"
    
    resp = client.post("/company/campaigns/", json=payload, headers=headers)
    assert resp.status_code == 400
    assert "not supported" in str(resp.json()).lower()


@patch("app.api.company.campaigns.CompanyRepository")
@patch("app.middleware.limits.CompanyRepository")
@patch("app.api.company.campaigns.StrategyRepository")
@patch("app.api.company.campaigns.CampaignRepository")
def test_campaign_create_invalid_mixed_composition_total(mock_camp_repo, mock_strat_repo, mock_limits_comp_repo, mock_comp_repo, client, company_token):
    headers = {"Authorization": f"Bearer {company_token}"}
    
    mock_comp_instance = AsyncMock()
    mock_comp_instance.get_by_id.return_value = {
        "_id": str(ObjectId()),
        "status": "active",
        "subscription": {"status": "active"},
        "limits": {"max_campaigns": 10},
        "usage": {"campaigns_used": 0},
        "allowed_strategies": ["mixed_strat"]
    }
    mock_comp_repo.return_value = mock_comp_instance
    mock_limits_comp_repo.return_value = mock_comp_instance
    
    mock_strat_instance = AsyncMock()
    mock_strat_instance.get_latest_version.return_value = {
        "strategy_id": "mixed_strat",
        "name": "Mixed Strat",
        "description": "desc",
        "version": 1,
        "is_active": True,
        "applicable_interview_types": ["mixed"],
        "min_questions": 5,
        "target_questions": 10,
        "max_questions": 15,
        "max_questions_per_topic": 3,
        "max_followups_per_topic": 2,
        "strong_threshold": 0.8,
        "acceptable_threshold": 0.6,
        "weak_threshold": 0.4,
        "topic_selection_policy": {},
        "difficulty_policy": {},
        "followup_policy": {},
        "gap_policy": {},
        "completion_policy": {},
        "company_override_bounds": {}
    }
    mock_strat_repo.return_value = mock_strat_instance
    
    payload = get_base_campaign_payload()
    payload["strategy_id"] = "mixed_strat"
    payload["interview_type"] = "mixed"
    
    # Over 100%
    payload["mixed_composition"] = {
        "technical": 0.6,
        "resume_experience": 0.5,
        "hr_behavioral": 0,
        "situational_case": 0
    }
    resp = client.post("/company/campaigns/", json=payload, headers=headers)
    assert resp.status_code == 422
    assert "sum to exactly 1.0" in str(resp.json())


@patch("app.api.company.campaigns.CompanyRepository")
@patch("app.middleware.limits.CompanyRepository")
@patch("app.api.company.campaigns.StrategyRepository")
@patch("app.api.company.campaigns.CampaignRepository")
def test_campaign_create_mixed_composition_without_mixed_type(mock_camp_repo, mock_strat_repo, mock_limits_comp_repo, mock_comp_repo, client, company_token):
    headers = {"Authorization": f"Bearer {company_token}"}
    
    mock_comp_instance = AsyncMock()
    mock_comp_instance.get_by_id.return_value = {
        "_id": str(ObjectId()),
        "status": "active",
        "subscription": {"status": "active"},
        "limits": {"max_campaigns": 10},
        "usage": {"campaigns_used": 0},
        "allowed_strategies": ["Test Strat"]
    }
    mock_comp_repo.return_value = mock_comp_instance
    mock_limits_comp_repo.return_value = mock_comp_instance
    
    mock_strat_instance = AsyncMock()
    mock_strat_instance.get_latest_version.return_value = {
        "strategy_id": "test_strat_1",
        "name": "Test Strat",
        "description": "desc",
        "version": 1,
        "is_active": True,
        "applicable_interview_types": ["technical"],
        "min_questions": 5,
        "target_questions": 10,
        "max_questions": 15,
        "max_questions_per_topic": 3,
        "max_followups_per_topic": 2,
        "strong_threshold": 0.8,
        "acceptable_threshold": 0.6,
        "weak_threshold": 0.4,
        "topic_selection_policy": {},
        "difficulty_policy": {},
        "followup_policy": {},
        "gap_policy": {},
        "completion_policy": {},
        "company_override_bounds": {}
    }
    mock_strat_repo.return_value = mock_strat_instance
    
    payload = get_base_campaign_payload()
    payload["strategy_id"] = "test_strat_1"
    payload["interview_type"] = "technical"
    payload["mixed_composition"] = {
        "technical": 1.0,
        "resume_experience": 0.0,
        "hr_behavioral": 0.0,
        "situational_case": 0.0
    }
    
    resp = client.post("/company/campaigns/", json=payload, headers=headers)
    assert resp.status_code == 400
    assert "only allowed for mixed interview type" in str(resp.json()).lower()


@patch("app.api.company.campaigns.CompanyRepository")
@patch("app.middleware.limits.CompanyRepository")
@patch("app.api.company.campaigns.StrategyRepository")
@patch("app.api.company.campaigns.CampaignRepository")
def test_campaign_create_budget_override_bounds(mock_camp_repo, mock_strat_repo, mock_limits_comp_repo, mock_comp_repo, client, company_token):
    headers = {"Authorization": f"Bearer {company_token}"}
    
    mock_comp_instance = AsyncMock()
    mock_comp_instance.get_by_id.return_value = {
        "_id": str(ObjectId()),
        "status": "active",
        "subscription": {"status": "active"},
        "limits": {"max_campaigns": 10},
        "usage": {"campaigns_used": 0},
        "allowed_strategies": ["Test Strat"]
    }
    mock_comp_repo.return_value = mock_comp_instance
    mock_limits_comp_repo.return_value = mock_comp_instance
    
    mock_strat_instance = AsyncMock()
    mock_strat_instance.get_latest_version.return_value = {
        "strategy_id": "test_strat_1",
        "name": "Test Strat",
        "description": "desc",
        "version": 1,
        "is_active": True,
        "applicable_interview_types": ["technical"],
        "min_questions": 5,
        "target_questions": 10,
        "max_questions": 15,
        "max_questions_per_topic": 3,
        "max_followups_per_topic": 2,
        "strong_threshold": 0.8,
        "acceptable_threshold": 0.6,
        "weak_threshold": 0.4,
        "topic_selection_policy": {},
        "difficulty_policy": {},
        "followup_policy": {},
        "gap_policy": {},
        "completion_policy": {},
        "company_override_bounds": {
            "target_questions_min_delta": -2, # min allowed target: 8
            "target_questions_max_delta": 2,  # max allowed target: 12
            "allowed_difficulty_bands": ["medium"]
        }
    }
    mock_strat_repo.return_value = mock_strat_instance
    
    payload = get_base_campaign_payload()
    payload["strategy_id"] = "test_strat_1"
    payload["interview_type"] = "technical"
    
    # Test below min
    payload["budget_override"] = {"target_questions": 7}
    resp = client.post("/company/campaigns/", json=payload, headers=headers)
    assert resp.status_code == 400
    assert "outside allowed bounds" in str(resp.json())
    
    # Test above max
    payload["budget_override"] = {"target_questions": 13}
    resp = client.post("/company/campaigns/", json=payload, headers=headers)
    assert resp.status_code == 400
    assert "outside allowed bounds" in str(resp.json())


@patch("app.api.company.campaigns.CompanyRepository")
@patch("app.middleware.limits.CompanyRepository")
@patch("app.api.company.campaigns.StrategyRepository")
@patch("app.api.company.campaigns.CampaignRepository")
def test_campaign_create_invalid_difficulty_band(mock_camp_repo, mock_strat_repo, mock_limits_comp_repo, mock_comp_repo, client, company_token):
    headers = {"Authorization": f"Bearer {company_token}"}
    
    mock_comp_instance = AsyncMock()
    mock_comp_instance.get_by_id.return_value = {
        "_id": str(ObjectId()),
        "status": "active",
        "subscription": {"status": "active"},
        "limits": {"max_campaigns": 10},
        "usage": {"campaigns_used": 0},
        "allowed_strategies": ["Test Strat"]
    }
    mock_comp_repo.return_value = mock_comp_instance
    mock_limits_comp_repo.return_value = mock_comp_instance
    
    mock_strat_instance = AsyncMock()
    mock_strat_instance.get_latest_version.return_value = {
        "strategy_id": "test_strat_1",
        "name": "Test Strat",
        "description": "desc",
        "version": 1,
        "is_active": True,
        "applicable_interview_types": ["technical"],
        "min_questions": 5,
        "target_questions": 10,
        "max_questions": 15,
        "max_questions_per_topic": 3,
        "max_followups_per_topic": 2,
        "strong_threshold": 0.8,
        "acceptable_threshold": 0.6,
        "weak_threshold": 0.4,
        "topic_selection_policy": {},
        "difficulty_policy": {},
        "followup_policy": {},
        "gap_policy": {},
        "completion_policy": {},
        "company_override_bounds": {
            "target_questions_min_delta": -2,
            "target_questions_max_delta": 2,
            "allowed_difficulty_bands": ["medium"]
        }
    }
    mock_strat_repo.return_value = mock_strat_instance
    
    payload = get_base_campaign_payload()
    payload["strategy_id"] = "test_strat_1"
    payload["interview_type"] = "technical"
    payload["difficulty_band"] = "hard"
    
    resp = client.post("/company/campaigns/", json=payload, headers=headers)
    assert resp.status_code == 400
    assert "not allowed" in str(resp.json())


@patch("app.api.company.campaigns.CompanyRepository")
@patch("app.middleware.limits.CompanyRepository")
@patch("app.api.company.campaigns.StrategyRepository")
@patch("app.api.company.campaigns.CampaignRepository")
def test_campaign_create_invalid_language_and_voice(mock_camp_repo, mock_strat_repo, mock_limits_comp_repo, mock_comp_repo, client, company_token):
    headers = {"Authorization": f"Bearer {company_token}"}
    
    mock_comp_instance = AsyncMock()
    mock_comp_instance.get_by_id.return_value = {
        "_id": str(ObjectId()),
        "status": "active",
        "subscription": {"status": "active"},
        "limits": {"max_campaigns": 10},
        "usage": {"campaigns_used": 0},
        "allowed_strategies": ["Test Strat"],
        "allowed_languages": ["en"],
        "allowed_voices": ["voice1"]
    }
    mock_comp_repo.return_value = mock_comp_instance
    mock_limits_comp_repo.return_value = mock_comp_instance
    
    mock_strat_instance = AsyncMock()
    mock_strat_instance.get_latest_version.return_value = {
        "strategy_id": "test_strat_1",
        "name": "Test Strat",
        "description": "desc",
        "version": 1,
        "is_active": True,
        "applicable_interview_types": ["technical"],
        "min_questions": 5,
        "target_questions": 10,
        "max_questions": 15,
        "max_questions_per_topic": 3,
        "max_followups_per_topic": 2,
        "strong_threshold": 0.8,
        "acceptable_threshold": 0.6,
        "weak_threshold": 0.4,
        "topic_selection_policy": {},
        "difficulty_policy": {},
        "followup_policy": {},
        "gap_policy": {},
        "completion_policy": {},
        "company_override_bounds": {}
    }
    mock_strat_repo.return_value = mock_strat_instance
    
    payload = get_base_campaign_payload()
    payload["strategy_id"] = "test_strat_1"
    payload["interview_type"] = "technical"
    
    # Test invalid language
    payload["language"] = "fr"
    resp = client.post("/company/campaigns/", json=payload, headers=headers)
    assert resp.status_code == 403
    assert "language not allowed" in str(resp.json()).lower()
    
    # Test invalid voice
    payload["language"] = "en"
    payload["voice_id"] = "voice2"
    resp = client.post("/company/campaigns/", json=payload, headers=headers)
    assert resp.status_code == 422
    assert "is not allowed" in str(resp.json()).lower()


# ─────────────────────────────────────────────────────────────────────────────
# update_campaign (PATCH /company/campaigns/{id}) -- same allowed_strategies
# display-name-vs-strategy_id-slug bug, same fix, mirrored here.
# ─────────────────────────────────────────────────────────────────────────────

@patch("app.api.company.campaigns.CompanyRepository")
@patch("app.api.company.campaigns.StrategyRepository")
@patch("app.api.company.campaigns.CampaignRepository")
def test_campaign_update_valid_strategy_matched_by_name(mock_camp_repo, mock_strat_repo, mock_comp_repo, client):
    company_id = str(ObjectId())
    token = create_access_token(user_id=company_id, role="company", company_id=company_id)
    headers = {"Authorization": f"Bearer {token}"}

    mock_camp_instance = AsyncMock()
    mock_camp_instance.get_by_id.return_value = {
        "_id": str(ObjectId()),
        "company_id": company_id,
    }
    mock_camp_instance.update.return_value = True
    mock_camp_repo.return_value = mock_camp_instance

    mock_comp_instance = AsyncMock()
    mock_comp_instance.get_by_id.return_value = {
        "_id": company_id,
        "status": "active",
        "subscription": {"status": "active"},
        # Real company documents list allowed strategies by display NAME.
        "allowed_strategies": ["Test Strat"],
    }
    mock_comp_repo.return_value = mock_comp_instance

    mock_strat_instance = AsyncMock()
    mock_strat_instance.get_latest_version.return_value = {
        "strategy_id": "test_strat_1",
        "name": "Test Strat",
        "description": "desc",
        "version": 1,
        "is_active": True,
        "applicable_interview_types": ["technical"],
        "min_questions": 5,
        "target_questions": 10,
        "max_questions": 15,
        "max_questions_per_topic": 3,
        "max_followups_per_topic": 2,
        "strong_threshold": 0.8,
        "acceptable_threshold": 0.6,
        "weak_threshold": 0.4,
        "topic_selection_policy": {},
        "difficulty_policy": {},
        "followup_policy": {},
        "gap_policy": {},
        "completion_policy": {},
        "company_override_bounds": {},
    }
    mock_strat_repo.return_value = mock_strat_instance

    resp = client.patch(
        "/company/campaigns/camp1",
        json={"strategy_id": "test_strat_1", "interview_type": "technical"},
        headers=headers,
    )
    assert resp.status_code == 200, resp.json()


@patch("app.api.company.campaigns.CompanyRepository")
@patch("app.api.company.campaigns.StrategyRepository")
@patch("app.api.company.campaigns.CampaignRepository")
def test_campaign_update_strategy_not_entitled_is_rejected(mock_camp_repo, mock_strat_repo, mock_comp_repo, client):
    company_id = str(ObjectId())
    token = create_access_token(user_id=company_id, role="company", company_id=company_id)
    headers = {"Authorization": f"Bearer {token}"}

    mock_camp_instance = AsyncMock()
    mock_camp_instance.get_by_id.return_value = {
        "_id": str(ObjectId()),
        "company_id": company_id,
    }
    mock_camp_repo.return_value = mock_camp_instance

    mock_comp_instance = AsyncMock()
    mock_comp_instance.get_by_id.return_value = {
        "_id": company_id,
        "status": "active",
        "subscription": {"status": "active"},
        "allowed_strategies": ["Allowed Strategy"],
    }
    mock_comp_repo.return_value = mock_comp_instance

    mock_strat_instance = AsyncMock()
    mock_strat_instance.get_latest_version.return_value = {
        "strategy_id": "disallowed_strat",
        "name": "Disallowed Strategy",
        "is_active": True,
    }
    mock_strat_repo.return_value = mock_strat_instance

    resp = client.patch(
        "/company/campaigns/camp1",
        json={"strategy_id": "disallowed_strat"},
        headers=headers,
    )
    assert resp.status_code == 403
    assert "strategy not allowed" in str(resp.json()).lower()
