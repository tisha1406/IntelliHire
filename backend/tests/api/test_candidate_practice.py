import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from bson import ObjectId
from datetime import datetime, UTC
from app.auth.jwt_handler import TokenPayload
from app.services.candidate_portal_service import CandidatePortalService
from app.ai_interview.transport.services.session_creation_service import SessionCreationService

@pytest_asyncio.fixture
def mock_candidate_repo():
    repo = AsyncMock()
    repo.get_by_id.return_value = {
        "_id": ObjectId(),
        "campaign_id": "mock_campaign_id"
    }
    return repo

@pytest_asyncio.fixture
def mock_workflow_repo():
    return AsyncMock()

@pytest_asyncio.fixture
def mock_activity_repo():
    return AsyncMock()

@pytest_asyncio.fixture
def mock_session_creation_service():
    service = AsyncMock(spec=SessionCreationService)
    service.create_session.return_value = {
        "session_id": "mock_session_id",
        "state": "CREATED",
        "mode_id": "technical",
        "topics_count": 3,
        "total_question_budget": 10,
        "min_questions": 5
    }
    return service

@pytest.mark.asyncio
async def test_start_practice_creates_real_session(
    mock_candidate_repo,
    mock_workflow_repo,
    mock_activity_repo,
    mock_session_creation_service
):
    service = CandidatePortalService()
    service.candidate_repo = mock_candidate_repo
    service.workflow_repo = mock_workflow_repo
    service.activity_repo = mock_activity_repo

    candidate_id_hex = str(ObjectId())
    campaign_id_hex = str(ObjectId())

    token = TokenPayload(
        sub="user_id",
        user_id="user_id",
        email="test@test.com",
        role="candidate",
        candidate_id=candidate_id_hex,
        company_id="mock_company_id",
        campaign_id=campaign_id_hex,
        iat=int(datetime.now(UTC).timestamp()),
        exp=9999999999
    )

    result = await service.start_practice(token, mock_session_creation_service)

    # Verify workflow and activity log updated
    mock_workflow_repo.set_step_status.assert_called_once()
    assert mock_workflow_repo.set_step_status.call_args[0][0] == candidate_id_hex
    assert mock_workflow_repo.set_step_status.call_args[0][2] == "PRACTICE_AVAILABLE"
    
    mock_activity_repo.create.assert_called_once()

    # Verify campaign lookup
    mock_candidate_repo.get_by_id.assert_called_once_with(candidate_id_hex)

    # Verify session creation was called
    mock_session_creation_service.create_session.assert_called_once_with(token, "mock_campaign_id", is_practice=True)

    # Verify result shape matches CreateSessionResponse fields
    assert result["session_id"] == "mock_session_id"
    assert result["state"] == "CREATED"
    assert result["mode_id"] == "technical"
    assert result["topics_count"] == 3
