import pytest
from unittest.mock import AsyncMock, patch
from app.ai_interview.persistence.repository import InterviewSessionRepository
from app.ai_interview.persistence.exceptions import (
    OptimisticConcurrencyError,
    SessionNotFoundError,
    IdempotencyConflictError
)
from app.ai_interview.schemas.session import InterviewSessionSchema

@pytest.fixture
def mock_collection():
    return AsyncMock()

@pytest.fixture
def repo(mock_collection):
    return InterviewSessionRepository(mock_collection)

@pytest.fixture
def mock_session():
    # Helper to return a basic session
    from app.ai_interview.schemas.blueprint import InterviewBlueprint
    blueprint = InterviewBlueprint(
        blueprint_version="1.0",
        total_question_budget=5,
        min_questions=2,
        max_questions=5,
        emergency_max_questions=7,
        topics=[]
    )
    return InterviewSessionSchema(
        session_id="session-123",
        candidate_id="c-123",
        company_id="comp-123",
        campaign_id="camp-123",
        mode_id="mode-1",
        mode_version=1,
        blueprint=blueprint,
        created_at="2026-09-01T00:00:00Z"
    )

@pytest.mark.asyncio
async def test_save_success(repo, mock_collection, mock_session):
    mock_collection.update_one.return_value.matched_count = 1
    
    await repo.save(mock_session, expected_version=1)
    
    mock_collection.update_one.assert_called_once()
    args, kwargs = mock_collection.update_one.call_args
    query = args[0]
    
    assert query["session_id"] == "session-123"
    assert query["version"] == 1
    assert mock_session.version == 2

@pytest.mark.asyncio
async def test_save_stale_write_raises_occ(repo, mock_collection, mock_session):
    # matched_count = 0 implies either not found or OCC conflict
    mock_collection.update_one.return_value.matched_count = 0
    # count_documents without version returns 1 (it exists)
    # count_documents with version returns 0 (stale write)
    async def fake_count_documents(q):
        if "version" in q:
            return 0
        return 1
    mock_collection.count_documents.side_effect = fake_count_documents
    
    with pytest.raises(OptimisticConcurrencyError, match="Stale write"):
        await repo.save(mock_session, expected_version=1)

@pytest.mark.asyncio
async def test_save_not_found_raises(repo, mock_collection, mock_session):
    mock_collection.update_one.return_value.matched_count = 0
    mock_collection.count_documents.return_value = 0 # doesn't exist at all
    
    with pytest.raises(SessionNotFoundError):
        await repo.save(mock_session, expected_version=1)
