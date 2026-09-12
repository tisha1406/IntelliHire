import pytest
import uuid
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock
from app.ai_interview.persistence.repository import InterviewSessionRepository
from app.ai_interview.persistence.exceptions import FencingTokenError, OptimisticConcurrencyError
from app.ai_interview.schemas.session import InterviewSessionSchema, OperationClaim

@pytest.fixture
def mock_collection():
    return AsyncMock()

@pytest.fixture
def repo(mock_collection):
    return InterviewSessionRepository(mock_collection)

@pytest.mark.asyncio
async def test_stale_worker_cannot_finalize_after_claim_replacement(repo, mock_collection):
    """
    Fencing Token Test:
    Worker A acquires claim. Worker A stalls.
    Worker B acquires claim.
    Worker A wakes up and attempts to save (finalize) with Worker A's claim_id.
    It MUST raise FencingTokenError, preventing overwrite.
    """
    from app.ai_interview.schemas.blueprint import InterviewBlueprint
    blueprint = InterviewBlueprint(
        blueprint_version="1.0",
        total_question_budget=5,
        min_questions=2,
        max_questions=5,
        emergency_max_questions=7,
        topics=[]
    )
    
    session = InterviewSessionSchema(
        session_id="session-123",
        candidate_id="c-123",
        company_id="comp-123",
        campaign_id="camp-123",
        mode_id="mode-1",
        mode_version=1,
        blueprint=blueprint,
        created_at=datetime.now(timezone.utc)
    )
    
    worker_a_claim_id = str(uuid.uuid4())
    session.generation_claim = OperationClaim(
        claim_id=worker_a_claim_id,
        claimed_at=datetime.now(timezone.utc),
        expires_at=datetime.now(timezone.utc) + timedelta(seconds=60)
    )
    
    # Attempt to save. The update fails OCC/fencing.
    mock_collection.update_one.return_value.matched_count = 0
    mock_collection.count_documents.return_value = 1 # The document exists!
    
    # Simulate DB version matches, but fencing token fails
    async def fake_count_documents(q):
        if "generation_claim.claim_id" in q:
            return 0 # The DB's claim_id was overwritten by Worker B!
        return 1
    mock_collection.count_documents.side_effect = fake_count_documents
    
    # Finalize generation by passing fencing claim id
    with pytest.raises(FencingTokenError, match="Operation finalized by stale worker who lost the lease"):
        await repo.save(session, expected_version=10, generation_fencing_id=worker_a_claim_id)

@pytest.mark.asyncio
async def test_stale_save_cannot_erase_active_claim(repo, mock_collection):
    """
    Test that a full aggregate save (Worker A) without an active claim will hit an OCC exception
    if a concurrent worker (Worker B) has taken a claim (which bumps the version).
    Worker A's state is stale, Worker B's active claim remains safe.
    """
    from app.ai_interview.schemas.blueprint import InterviewBlueprint
    blueprint = InterviewBlueprint(
        blueprint_version="1.0",
        total_question_budget=5,
        min_questions=2,
        max_questions=5,
        emergency_max_questions=7,
        topics=[]
    )
    session = InterviewSessionSchema(
        session_id="session-123",
        candidate_id="c-123",
        company_id="comp-123",
        campaign_id="camp-123",
        mode_id="mode-1",
        mode_version=1,
        blueprint=blueprint,
        created_at=datetime.now(timezone.utc)
    )
    
    # Worker A loads V10 (generation_claim = None)
    # Worker B claims evaluation (DB bumps to V11)
    
    # Worker A attempts to save V10
    mock_collection.update_one.return_value.matched_count = 0
    
    async def fake_count(q):
        if "version" in q:
            return 0 # The DB is V11, Worker A expects V10
        return 1
    mock_collection.count_documents.side_effect = fake_count
    
    with pytest.raises(OptimisticConcurrencyError, match="Stale write"):
        await repo.save(session, expected_version=10)
