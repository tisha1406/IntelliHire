import pytest
import uuid
import asyncio
from datetime import datetime, timezone

from app.ai_interview.schemas.blueprint import InterviewBlueprint
from app.ai_interview.schemas.session import InterviewSessionSchema, OperationClaim
from app.ai_interview.question_engine.schemas import QuestionRecord, QuestionStatus, QuestionType, DifficultyLevel
from app.ai_interview.core.enums import InterviewState, TopicState
from app.ai_interview.runtime import SessionInitializer, RuntimeController, RuntimeAction
from app.ai_interview.persistence.exceptions import ClaimAlreadyHeldError, FencingTokenError, OptimisticConcurrencyError

@pytest.mark.mongodb
@pytest.mark.asyncio
async def test_question_generation_crash_recovery(real_repo):
    """
    Simulates a worker crash during question generation and successful recovery
    by another worker after the lease expires. Verifies the stale worker is fenced out.
    """
    blueprint = InterviewBlueprint(
        blueprint_version="1.0", total_question_budget=5, min_questions=2, max_questions=5, emergency_max_questions=7,
        topics=[{"topic_id": "topic_1", "topic_name": "Python", "source": "resume", "priority": 1}]
    )
    
    session = SessionInitializer.initialize(
        blueprint=blueprint, candidate_id="cand_1", company_id="comp_1", campaign_id="camp_1", mode_id="m_1", mode_version=1
    )
    session.session_id = str(uuid.uuid4())
    RuntimeController.execute_transition(session, RuntimeAction.INITIALIZE)
    RuntimeController.execute_transition(session, RuntimeAction.START)
    RuntimeController.execute_transition(session, RuntimeAction.ADVANCE_TOPIC)
    
    await real_repo.save(session, expected_version=0)
    
    # 1. Worker A claims generation with a tiny 1-second lease
    claim_a = await real_repo.claim_question_generation(session.session_id, expected_version=session.version, lease_seconds=1)
    worker_a_claim_id = claim_a.claim_id
    
    # 2. Worker A "crashes" (sleeps past lease expiration)
    session_a_memory = await real_repo.get_by_id(session.session_id)
    await asyncio.sleep(1.1)
    
    # 3. Worker B detects stale lease and claims successfully
    session_b_memory = await real_repo.get_by_id(session.session_id)
    claim_b = await real_repo.claim_question_generation(session.session_id, expected_version=session_b_memory.version, lease_seconds=10)
    worker_b_claim_id = claim_b.claim_id
    
    # Worker B finishes and saves
    q_b = QuestionRecord(
        record_id=str(uuid.uuid4()),
        session_id=session.session_id,
        turn_number=1,
        topic_id="topic_1",
        question_text="Worker B's Question",
        question_type=QuestionType.INITIAL,
        difficulty=DifficultyLevel.MEDIUM,
        status=QuestionStatus.DISPATCHED
    )
    session_b_memory = await real_repo.get_by_id(session.session_id)
    session_b_memory.question_history.append(q_b)
    session_b_memory.questions_asked_total += 1
    session_b_memory.topic_progress[0].questions_asked += 1
    session_b_memory.generation_claim = None
    
    await real_repo.save(session_b_memory, expected_version=session_b_memory.version, generation_fencing_id=worker_b_claim_id)
    
    # 4. Worker A wakes up and tries to save its work
    q_stale = QuestionRecord(
        record_id=str(uuid.uuid4()),
        session_id=session.session_id,
        turn_number=1,
        topic_id="topic_1",
        question_text="Worker A's Stale Question",
        question_type=QuestionType.INITIAL,
        difficulty=DifficultyLevel.MEDIUM,
        status=QuestionStatus.DISPATCHED
    )
    session_a_memory.question_history.append(q_stale)
    session_a_memory.questions_asked_total += 1
    session_a_memory.topic_progress[0].questions_asked += 1
    session_a_memory.generation_claim = None
    
    # Worker A attempts to finalize with its old fencing ID
    with pytest.raises(Exception) as excinfo:
        await real_repo.save(session_a_memory, expected_version=session_a_memory.version, generation_fencing_id=worker_a_claim_id)
        
    assert excinfo.type in [FencingTokenError, OptimisticConcurrencyError]
    
    # 5. Verify Database remains pristine with Worker B's result
    final_session = await real_repo.get_by_id(session.session_id)
    assert final_session.questions_asked_total == 1
    assert len(final_session.question_history) == 1
    assert final_session.question_history[0].question_text == "Worker B's Question"
    assert final_session.generation_claim is None
