import pytest
from unittest.mock import AsyncMock, MagicMock
from app.ai_interview.persistence.repository import InterviewSessionRepository
from app.ai_interview.core.enums import InterviewState
from app.ai_interview.schemas.session import InterviewSessionSchema

@pytest.fixture
def mock_collection():
    collection = MagicMock()
    collection.find_one = AsyncMock()
    return collection

@pytest.fixture
def repo(mock_collection):
    return InterviewSessionRepository(mock_collection)

@pytest.mark.asyncio
async def test_find_active_session_excludes_terminal_states(repo, mock_collection):
    mock_collection.find_one.return_value = None
    
    await repo.find_active_session("cand-1", "camp-1")
    
    mock_collection.find_one.assert_called_once()
    query = mock_collection.find_one.call_args[0][0]
    
    assert query["candidate_id"] == "cand-1"
    assert query["campaign_id"] == "camp-1"
    assert "state" in query
    assert "$nin" in query["state"]
    
    # Assert it uses the actual persisted enum values
    assert query["state"]["$nin"] == [InterviewState.COMPLETED.value, InterviewState.FAILED.value]

@pytest.mark.asyncio
async def test_find_active_session_with_mode_id(repo, mock_collection):
    mock_collection.find_one.return_value = None
    
    await repo.find_active_session("cand-1", "camp-1", mode_id="practice")
    
    mock_collection.find_one.assert_called_once()
    query = mock_collection.find_one.call_args[0][0]
    
    assert query["candidate_id"] == "cand-1"
    assert query["campaign_id"] == "camp-1"
    assert query["mode_id"] == "practice"
    assert "state" in query
    assert query["state"]["$nin"] == [InterviewState.COMPLETED.value, InterviewState.FAILED.value]

@pytest.mark.asyncio
async def test_find_active_session_returns_in_progress(repo, mock_collection):
    # Construct a valid dummy document
    dummy_doc = {
        "session_id": "sess-1",
        "candidate_id": "cand-1",
        "company_id": "comp-1",
        "campaign_id": "camp-1",
        "mode_id": "technical",
        "mode_version": 1,
        "state": InterviewState.IN_PROGRESS.value,
        "blueprint": {
            "blueprint_version": "1.0",
            "topics": [],
            "total_question_budget": 5,
            "min_questions": 3,
            "max_questions": 5,
            "emergency_max_questions": 6
        },
        "question_history": [],
        "created_at": "2026-09-26T12:00:00Z"
    }
    mock_collection.find_one.return_value = dummy_doc
    
    result = await repo.find_active_session("cand-1", "camp-1")
    
    assert result is not None
    assert result.session_id == "sess-1"
    assert result.state == InterviewState.IN_PROGRESS

@pytest.mark.asyncio
async def test_find_active_session_returns_none_if_not_found(repo, mock_collection):
    mock_collection.find_one.return_value = None
    result = await repo.find_active_session("cand-1", "camp-1")
    assert result is None
