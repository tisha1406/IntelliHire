import pytest
import uuid
from datetime import datetime, timezone

from app.ai_interview.schemas.blueprint import InterviewBlueprint
from app.ai_interview.schemas.session import InterviewSessionSchema, OperationClaim
from app.ai_interview.core.enums import InterviewState, TopicState
from app.ai_interview.runtime import SessionInitializer, RuntimeController, RuntimeAction
from app.ai_interview.persistence.exceptions import PersistenceInvariantError
from app.ai_interview.persistence.validator import SessionPersistenceValidator

@pytest.mark.mongodb
@pytest.mark.asyncio
async def test_terminal_session_immutability(real_repo):
    """
    Verifies that a completed interview cannot be mutated with active claims.
    The SessionPersistenceValidator enforces this.
    """
    blueprint = InterviewBlueprint(
        blueprint_version="1.0", total_question_budget=5, min_questions=2, max_questions=5, emergency_max_questions=7,
        topics=[{"topic_id": "topic_1", "topic_name": "Python", "source": "resume", "priority": 1}]
    )
    
    session = SessionInitializer.initialize(
        blueprint=blueprint, candidate_id="cand_1", company_id="comp_1", campaign_id="camp_1", mode_id="m_1", mode_version=1
    )
    session.session_id = str(uuid.uuid4())
    
    # Fast forward to completed
    session.state = InterviewState.COMPLETED
    session.completed_at = datetime.now(timezone.utc)
    
    # Simulate a rogue worker attaching a generation claim to a completed session
    session.generation_claim = OperationClaim(
        claim_id=str(uuid.uuid4()),
        claimed_at=datetime.now(timezone.utc),
        expires_at=datetime.now(timezone.utc)
    )
    
    with pytest.raises(PersistenceInvariantError, match="cannot retain active generation_claim"):
        await real_repo.save(session, expected_version=0)
