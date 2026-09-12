import pytest
import uuid
import asyncio

from app.ai_interview.schemas.blueprint import InterviewBlueprint
from app.ai_interview.schemas.session import InterviewSessionSchema, OperationClaim
from app.ai_interview.question_engine.schemas import QuestionRecord, QuestionStatus, QuestionType, DifficultyLevel
from app.ai_interview.answer_engine.schemas import EvaluationRecord, CoverageSignal, FollowUpSignal
from app.ai_interview.core.enums import InterviewState, TopicState
from app.ai_interview.runtime import SessionInitializer, RuntimeController, RuntimeAction
from app.ai_interview.persistence.exceptions import ClaimAlreadyHeldError, FencingTokenError, IdempotencyConflictError, OptimisticConcurrencyError, PersistenceInvariantError

@pytest.mark.mongodb
@pytest.mark.asyncio
async def test_duplicate_client_requests(real_repo):
    """
    Simulates a client submitting the same answer twice concurrently.
    Verifies that OCC, Leases, and Idempotency prevent duplicate evaluations.
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
    
    # Simulate Concurrent Request A and Request B for Evaluation
    # Request A succeeds
    claim_a = await real_repo.claim_evaluation(session.session_id, q1_id, expected_version=session.version, lease_seconds=10)
    req_a_claim_id = claim_a.claim_id
    
    # Request B fails to claim because A holds it (it would read the new version first if doing a retry)
    session_latest = await real_repo.get_by_id(session.session_id)
    with pytest.raises(ClaimAlreadyHeldError):
        await real_repo.claim_evaluation(session.session_id, q1_id, expected_version=session_latest.version, lease_seconds=10)
    
    # Request A completes evaluation and saves
    session_a = await real_repo.get_by_id(session.session_id)
    eval_a = EvaluationRecord(
        evaluation_id=str(uuid.uuid4()), question_record_id=q1_id, topic_id="topic_1",
        overall_score=1.0, qualitative_coverage_signal=CoverageSignal.QUALITATIVELY_COVERED, follow_up_signal=FollowUpSignal.NONE
    )
    session_a.evaluation_history.append(eval_a)
    session_a.question_history[0].status = QuestionStatus.EVALUATED
    session_a.question_history[0].evaluation_claim = None
    
    await real_repo.save(session_a, expected_version=session_a.version, evaluation_fencing_id=req_a_claim_id)
    
    # Simulate a scenario where Request B SOMEHOW bypassed the claim block and tries to save a duplicate eval
    # (e.g. if a bug in the application logic didn't check the claim)
    session_b_memory = await real_repo.get_by_id(session.session_id)
    session_b_memory.version = 1 # Old version
    eval_b = EvaluationRecord(
        evaluation_id=str(uuid.uuid4()), question_record_id=q1_id, topic_id="topic_1",
        overall_score=0.1, qualitative_coverage_signal=CoverageSignal.NOT_COVERED, follow_up_signal=FollowUpSignal.NONE
    )
    session_b_memory.evaluation_history.append(eval_b)
    
    # The persistence idempotency guard should reject this since there's already an evaluation for q1_id
    with pytest.raises(Exception) as excinfo:
        await real_repo.save(session_b_memory, expected_version=session_b_memory.version, idempotency_evaluation_question_id=q1_id)
        
    assert excinfo.type in [IdempotencyConflictError, OptimisticConcurrencyError, PersistenceInvariantError]
    
    # Verify final aggregate
    final_session = await real_repo.get_by_id(session.session_id)
    assert len(final_session.evaluation_history) == 1
    assert final_session.evaluation_history[0].overall_score == 1.0
