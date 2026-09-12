import pytest
import uuid
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock
from app.ai_interview.persistence.repository import InterviewSessionRepository
from app.ai_interview.persistence.exceptions import ClaimAlreadyHeldError
from app.ai_interview.schemas.session import InterviewSessionSchema, OperationClaim

@pytest.fixture
def mock_collection():
    return AsyncMock()

@pytest.fixture
def repo(mock_collection):
    return InterviewSessionRepository(mock_collection)

@pytest.mark.asyncio
async def test_concurrent_question_generation_allows_only_one_claim(repo, mock_collection):
    """
    Proves only one worker can claim an operation. The second worker receives ClaimAlreadyHeldError.
    """
    # Simulate Worker B trying to claim, but the query matched 0 docs because Worker A already claimed it
    mock_collection.update_one.return_value.modified_count = 0
    
    # And the reason it failed is that it's actively held
    async def fake_count_documents(q):
        return 1 # Active lease exists
    mock_collection.count_documents.side_effect = fake_count_documents
    
    with pytest.raises(ClaimAlreadyHeldError, match="Generation lease is actively held by another worker"):
        await repo.claim_question_generation("session-123", expected_version=5)

@pytest.mark.asyncio
async def test_expired_evaluation_claim_can_be_reclaimed(repo, mock_collection):
    """
    Proves that if an old worker crashed and the lease expired, a new worker can successfully reclaim it.
    """
    # The atomic update query includes `$or` logic to allow claiming if expires_at < now.
    mock_collection.update_one.return_value.modified_count = 1
    
    claim = await repo.claim_evaluation("session-123", "q-123", expected_version=5)
    
    assert claim is not None
    assert claim.claim_id is not None
    
    args, kwargs = mock_collection.update_one.call_args
    query = args[0]
    
    # Assert the query explicitly checks the expiration logic!
    assert "$or" in query
    clauses = query["$or"]
    
    # Clause 1: no claim exists yet
    assert {"question_history.status": {"$in": ["dispatched", "answer_received"]}} in clauses
    
    # Clause 2: claim exists but is expired!
    clause2 = clauses[1]
    assert clause2["question_history.status"] == "evaluating"
    assert "$lt" in clause2["question_history.evaluation_claim.expires_at"]
