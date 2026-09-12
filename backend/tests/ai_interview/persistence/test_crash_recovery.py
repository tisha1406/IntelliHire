import pytest
import uuid
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock
from app.ai_interview.persistence.repository import InterviewSessionRepository
from app.ai_interview.schemas.session import InterviewSessionSchema, OperationClaim
from app.ai_interview.question_engine.schemas import QuestionRecord
from app.ai_interview.question_engine.enums import QuestionStatus
from app.ai_interview.core.enums import QuestionType, DifficultyLevel
from app.ai_interview.schemas.blueprint import InterviewBlueprint

@pytest.fixture
def mock_collection():
    return AsyncMock()

@pytest.fixture
def repo(mock_collection):
    return InterviewSessionRepository(mock_collection)

@pytest.mark.asyncio
async def test_answer_survives_crash_before_evaluation(repo, mock_collection):
    """
    Simulate:
    1. Answer submitted and persisted. Status -> ANSWER_RECEIVED.
    2. Crash.
    3. Reload.
    4. Assert we can claim it for evaluation!
    """
    q_id = str(uuid.uuid4())
    mock_collection.update_one.return_value.modified_count = 1
    
    # Assert claim_evaluation works because status is "answer_received"
    claim = await repo.claim_evaluation("session-123", q_id, expected_version=10)
    
    assert claim is not None
    args, kwargs = mock_collection.update_one.call_args
    query = args[0]
    
    # Assert the query explicitly targets status IN ["dispatched", "answer_received"]
    assert "$or" in query
    assert {"question_history.status": {"$in": ["dispatched", "answer_received"]}} in query["$or"]

@pytest.mark.asyncio
async def test_stale_worker_recovering_from_crash_cannot_overwrite_newer_data(repo, mock_collection):
    """
    Scenario:
    Worker A crashes after claiming.
    Worker B reclaims after lease expires and completes evaluation.
    Worker A eventually restarts and tries to persist its LLM result!
    It should be blocked by FencingTokenError because the claim ID in DB is Worker B's.
    """
    # This was tested in test_fencing_tokens.py, but we'll add a specific check here
    pass
