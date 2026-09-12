import pytest
import uuid
import asyncio
from datetime import datetime, timezone

from app.ai_interview.schemas.blueprint import InterviewBlueprint
from app.ai_interview.schemas.session import InterviewSessionSchema, OperationClaim
from app.ai_interview.question_engine.schemas import QuestionRecord, QuestionStatus, QuestionType, DifficultyLevel
from app.ai_interview.core.enums import InterviewState, TopicState
from app.ai_interview.runtime import SessionInitializer, RuntimeController, RuntimeAction
from app.ai_interview.persistence.exceptions import ClaimAlreadyHeldError

@pytest.mark.mongodb
@pytest.mark.asyncio
async def test_double_question_generation(real_repo):
    """
    Simulates a client double-clicking 'Next Question'.
    Verifies exactly one question claim succeeds and exactly one question is persisted.
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
    
    # Request A succeeds
    claim_a = await real_repo.claim_question_generation(session.session_id, expected_version=session.version, lease_seconds=10)
    req_a_claim_id = claim_a.claim_id
    
    # Request B fails immediately since A holds the lease
    session_latest = await real_repo.get_by_id(session.session_id)
    with pytest.raises(ClaimAlreadyHeldError):
        await real_repo.claim_question_generation(session.session_id, expected_version=session_latest.version, lease_seconds=10)
    
    # Request A finalizes
    session_a = await real_repo.get_by_id(session.session_id)
    q1 = QuestionRecord(
        record_id=str(uuid.uuid4()), session_id=session.session_id, turn_number=1, topic_id="topic_1", question_text="What is PEP8?",
        question_type=QuestionType.INITIAL, difficulty=DifficultyLevel.MEDIUM, status=QuestionStatus.DISPATCHED
    )
    session_a.question_history.append(q1)
    session_a.questions_asked_total += 1
    session_a.topic_progress[0].questions_asked += 1
    session_a.topic_progress[0].state = TopicState.IN_PROGRESS
    session_a.generation_claim = None
    
    await real_repo.save(session_a, expected_version=session_a.version, generation_fencing_id=req_a_claim_id)
    
    final_session = await real_repo.get_by_id(session.session_id)
    assert len(final_session.question_history) == 1
    assert final_session.generation_claim is None
