import pytest
import uuid
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock
from app.ai_interview.persistence.repository import InterviewSessionRepository
from app.ai_interview.persistence.exceptions import IdempotencyConflictError
from app.ai_interview.schemas.session import InterviewSessionSchema, OperationClaim

@pytest.fixture
def mock_collection():
    return AsyncMock()

@pytest.fixture
def repo(mock_collection):
    return InterviewSessionRepository(mock_collection)

@pytest.mark.asyncio
async def test_duplicate_evaluation_is_not_committed_twice(repo, mock_collection):
    """
    Simulate Worker A and Worker B evaluating the exact same question simultaneously.
    Worker A saves successfully. Worker B attempts to save the same Evaluation.
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
    
    # Simulate saving an evaluation! The evaluation_history array gets checked!
    # Let's say Worker B is trying to save EvaluationRecord X.
    # The DB already received Worker A's save which contained EvaluationRecord X.
    
    mock_collection.update_one.return_value.matched_count = 0
    # Simulate DB version matches
    async def fake_count_documents(q):
        # We need to simulate that the version changed (so occ fails if checked),
        # but the idempotency check passes (so it detects duplicate)
        if "evaluation_history.question_record_id" in q:
            return 1 
        if "version" not in q and "generation_claim.claim_id" not in q and "question_history.evaluation_claim.claim_id" not in q:
            return 1 # session exists
        return 0 # simulate version moved forward for occ and fencing
    mock_collection.count_documents.side_effect = fake_count_documents
    
    from app.ai_interview.question_engine.schemas import QuestionRecord
    from app.ai_interview.question_engine.enums import QuestionStatus
    from app.ai_interview.core.enums import QuestionType, DifficultyLevel
    from app.ai_interview.answer_engine.schemas import EvaluationRecord
    from app.ai_interview.answer_engine.enums import CoverageSignal, FollowUpSignal
    
    q_id = str(uuid.uuid4())
    session.question_history.append(QuestionRecord(
        record_id=q_id,
        session_id="session-123",
        turn_number=1,
        topic_id="t1",
        question_text="Q1",
        question_type=QuestionType.INITIAL,
        difficulty=DifficultyLevel.MEDIUM,
        status=QuestionStatus.EVALUATING
    ))
    session.questions_asked_total = 1
    session.evaluation_history.append(EvaluationRecord(
        evaluation_id=str(uuid.uuid4()),
        question_record_id=q_id,
        topic_id="t1",
        overall_score=0.9,
        qualitative_coverage_signal=CoverageSignal.QUALITATIVELY_COVERED,
        follow_up_signal=FollowUpSignal.NONE
    ))
    
    # We pass evaluation_fencing_id so that fencing falls through, allowing idempotency to be checked
    with pytest.raises(IdempotencyConflictError, match="Database rejected update due to embedded idempotency guard"):
        await repo.save(session, expected_version=10, evaluation_fencing_id="claim-1", idempotency_evaluation_question_id=q_id)
