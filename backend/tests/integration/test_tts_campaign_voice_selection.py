import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient
from app.main import app
from app.auth.jwt_handler import create_access_token
import base64

client = TestClient(app)

@pytest.fixture
def auth_headers():
    token = create_access_token(user_id="test_cand", role="CANDIDATE", candidate_id="test_cand")
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def company_headers():
    token = create_access_token(user_id="test_company", role="COMPANY")
    return {"Authorization": f"Bearer {token}"}

@pytest.mark.asyncio
@pytest.mark.parametrize("voice_id", ["shubh", "simran", "rohan", "ishita", "sunny"])
async def test_campaign_voice_passed_to_sarvam(voice_id, auth_headers):
    mock_campaign = MagicMock()
    mock_campaign.voice_id = voice_id
    mock_campaign.language = "English"

    mock_session = MagicMock()
    mock_session.campaign_id = "c_1"
    del mock_session.voice_id
    
    mock_snapshot = MagicMock()
    mock_snapshot.current_question = MagicMock()
    mock_snapshot.current_question.record_id = "q_1"
    mock_snapshot.current_question.question_text = "Test question"
    
    mock_transport = AsyncMock()
    mock_transport.get_session_snapshot.return_value = mock_snapshot
    
    from app.api.interview import get_transport_service
    app.dependency_overrides[get_transport_service] = lambda: mock_transport

    with patch("app.api.interview.InterviewSessionRepository.get_by_id", new_callable=AsyncMock) as mock_get_session, \
         patch("app.api.interview.CampaignRepository.get_by_id", new_callable=AsyncMock) as mock_get_campaign, \
         patch("app.api.interview.get_database"), \
         patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_sarvam_post:
        
        mock_get_campaign.return_value = mock_campaign
        mock_get_session.return_value = mock_session
        
        # Mock Sarvam HTTP response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"audios": [base64.b64encode(b"audio").decode("utf-8")]}
        mock_sarvam_post.return_value = mock_response
        
        response = client.post(
            "/api/interview/sessions/test_session/questions/q_1/speech",
            headers=auth_headers
        )
        
        # Cleanup override
        app.dependency_overrides.pop(get_transport_service, None)
        
        assert response.status_code == 200
        
        # Verify Sarvam was called
        mock_sarvam_post.assert_called_once()
        call_kwargs = mock_sarvam_post.call_args.kwargs
        assert "json" in call_kwargs
        payload = call_kwargs["json"]
        
        # Verify EXACT payload matches campaign config
        assert payload["speaker"] == voice_id
        assert payload["model"] == "bulbul:v3"

@pytest.mark.asyncio
@pytest.mark.parametrize("invalid_voice", ["ritu", "manan", "unknown", ""])
async def test_invalid_voices_rejected_by_campaign_creation(company_headers, invalid_voice):
    payload = {
        "name": "Test Campaign",
        "interview_type": "technical",
        "strategy_id": "fixed_coverage",
        "interview_settings": {"duration": 45, "strictness": "medium", "type": "technical"},
        "voice_id": invalid_voice,
        "language": "English"
    }
    
    with patch("app.repositories.company_repository.CompanyRepository.get_by_id", new_callable=AsyncMock) as mock_get_company:
        # Mock the company doc with full access to all valid voices, ensuring only the campaign validation handles the rejection
        mock_get_company.return_value = {
            "allowed_languages": ["English"],
            "allowed_voices": ["shubh", "simran", "rohan", "ishita", "sunny"],
            "allowed_strategies": ["fixed_coverage"],
            "subscription": {"status": "active"},
            "limits": {"max_campaigns": 10},
            "usage": {"campaigns_created": 0}
        }
        
        # We don't need SubscriptionLimitsMiddleware patch since the mock handles it
        
        response = client.post(
            "/company/campaigns",
            headers=company_headers,
            json=payload
        )
        
        # Should be rejected
        assert response.status_code in [403, 422, 400]
        if response.status_code == 403:
            assert "Voice not allowed" in response.text
