import pytest
import uuid
import asyncio
from datetime import datetime, timezone

from app.ai_interview.schemas.blueprint import InterviewBlueprint
from app.ai_interview.schemas.session import InterviewSessionSchema, OperationClaim
from app.ai_interview.question_engine.schemas import QuestionRecord, QuestionStatus, QuestionType, DifficultyLevel
from app.ai_interview.answer_engine.schemas import EvaluationRecord, CoverageSignal, FollowUpSignal
from app.ai_interview.core.enums import InterviewState, TopicState
from app.ai_interview.runtime import SessionInitializer, RuntimeController, RuntimeAction
from app.ai_interview.persistence.exceptions import ClaimAlreadyHeldError, FencingTokenError, OptimisticConcurrencyError, PersistenceInvariantError

@pytest.mark.mongodb
@pytest.mark.asyncio
async def test_evaluation_crash_recovery_end_to_end(real_repo):
    """
    Simulates a worker crash during evaluation and successful recovery by another worker.
    Verifies that the stale worker cannot overwrite the recovered worker's evaluation.
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
    
    q1_id = str(uuid.uuid4())
    q1 = QuestionRecord(
        record_id=q1_id, session_id=session.session_id, turn_number=1, topic_id="topic_1", question_text="What is PEP8?",
        question_type=QuestionType.INITIAL, difficulty=DifficultyLevel.MEDIUM, status=QuestionStatus.ANSWER_RECEIVED
    )
    session.question_history.append(q1)
    session.questions_asked_total = 1
    session.topic_progress[0].questions_asked = 1
    session.topic_progress[0].state = TopicState.IN_PROGRESS
    
    await real_repo.save(session, expected_version=0)
    
    # 1. Worker A claims evaluation with tiny lease
    claim_a = await real_repo.claim_evaluation(session.session_id, q1_id, expected_version=session.version, lease_seconds=1)
    worker_a_claim_id = claim_a.claim_id
    
    # 2. Worker A crashes / stalls
    await asyncio.sleep(1.1)
    
    # 3. Worker B detects stale evaluation lease and claims it
    session_b_memory = await real_repo.get_by_id(session.session_id)
    claim_b = await real_repo.claim_evaluation(session.session_id, q1_id, expected_version=session_b_memory.version, lease_seconds=10)
    worker_b_claim_id = claim_b.claim_id
    
    # Worker B successfully evaluates answer
    session_b = await real_repo.get_by_id(session.session_id)
    
    eval_b = EvaluationRecord(
        evaluation_id=str(uuid.uuid4()),
        question_record_id=q1_id,
        topic_id="topic_1",
        overall_score=0.9,
        qualitative_coverage_signal=CoverageSignal.QUALITATIVELY_COVERED,
        follow_up_signal=FollowUpSignal.NONE
    )
    session_b.evaluation_history.append(eval_b)
    session_b.question_history[0].status = QuestionStatus.EVALUATED
    session_b.question_history[0].evaluation_claim = None
    
    session_b.topic_progress[0].coverage_score += 0.9
    
    # Worker B saves
    await real_repo.save(session_b, expected_version=session_b.version, evaluation_fencing_id=worker_b_claim_id)
    
    # 4. Worker A wakes up and tries to save its stale result
    session_a_memory = await real_repo.get_by_id(session.session_id) # reload to get valid shape to modify manually
    session_a_memory.version = 1 # Stale version when Worker A claimed
    
    eval_a = EvaluationRecord(
        evaluation_id=str(uuid.uuid4()),
        question_record_id=q1_id,
        topic_id="topic_1",
        overall_score=0.1, # Different score
        qualitative_coverage_signal=CoverageSignal.NOT_COVERED,
        follow_up_signal=FollowUpSignal.NONE
    )
    session_a_memory.evaluation_history.append(eval_a)
    
    with pytest.raises(Exception) as excinfo:
        await real_repo.save(session_a_memory, expected_version=session_a_memory.version, evaluation_fencing_id=worker_a_claim_id)
        
    assert excinfo.type in [FencingTokenError, OptimisticConcurrencyError, PersistenceInvariantError]
    
    # Verify final aggregate is B
    final_session = await real_repo.get_by_id(session.session_id)
    assert len(final_session.evaluation_history) == 1
    assert final_session.evaluation_history[0].overall_score == 0.9
