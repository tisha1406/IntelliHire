import pytest
import uuid
from datetime import datetime, timezone, timedelta
from app.ai_interview.persistence.validator import SessionPersistenceValidator
from app.ai_interview.persistence.exceptions import PersistenceInvariantError
from app.ai_interview.schemas.session import InterviewSessionSchema, OperationClaim
from app.ai_interview.question_engine.schemas import QuestionRecord
from app.ai_interview.question_engine.enums import QuestionStatus
from app.ai_interview.answer_engine.schemas import EvaluationRecord
from app.ai_interview.core.enums import InterviewState, QuestionType, DifficultyLevel
from app.ai_interview.schemas.blueprint import InterviewBlueprint
from app.ai_interview.answer_engine.enums import CoverageSignal, FollowUpSignal

@pytest.fixture
def base_session():
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
        created_at=datetime.now(timezone.utc)
    )

def test_questions_asked_total_invariant(base_session):
    base_session.questions_asked_total = 1
    # Len of question_history is 0!
    with pytest.raises(PersistenceInvariantError, match="does not match len"):
        SessionPersistenceValidator.validate(base_session)

def test_evaluation_references_missing_question(base_session):
    # Add an evaluation without a corresponding question
    er = EvaluationRecord(
        evaluation_id=str(uuid.uuid4()),
        question_record_id="q-ghost",
        topic_id="t1",
        overall_score=0.9,
        qualitative_coverage_signal=CoverageSignal.QUALITATIVELY_COVERED,
        follow_up_signal=FollowUpSignal.NONE
    )
    base_session.evaluation_history.append(er)
    
    with pytest.raises(PersistenceInvariantError, match="EvaluationRecord references non-existent QuestionRecord: q-ghost"):
        SessionPersistenceValidator.validate(base_session)

def test_terminal_session_rejects_active_claim(base_session):
    base_session.state = InterviewState.COMPLETED
    base_session.generation_claim = OperationClaim(
        claim_id="c-1",
        claimed_at=datetime.now(timezone.utc),
        expires_at=datetime.now(timezone.utc) + timedelta(seconds=60)
    )
    
    with pytest.raises(PersistenceInvariantError, match="cannot retain active generation_claim"):
        SessionPersistenceValidator.validate(base_session)

def test_duplicate_evaluation_fails_invariant(base_session):
    q_id = str(uuid.uuid4())
    qr = QuestionRecord(
        record_id=q_id,
        session_id=base_session.session_id,
        turn_number=1,
        topic_id="t1",
        question_text="Q1",
        question_type=QuestionType.INITIAL,
        difficulty=DifficultyLevel.MEDIUM,
        status=QuestionStatus.EVALUATED
    )
    base_session.question_history.append(qr)
    base_session.questions_asked_total = 1
    
    er1 = EvaluationRecord(
        evaluation_id=str(uuid.uuid4()),
        question_record_id=q_id,
        topic_id="t1",
        overall_score=0.9,
        qualitative_coverage_signal=CoverageSignal.QUALITATIVELY_COVERED,
        follow_up_signal=FollowUpSignal.NONE
    )
    er2 = EvaluationRecord(
        evaluation_id=str(uuid.uuid4()),
        question_record_id=q_id,
        topic_id="t1",
        overall_score=0.9,
        qualitative_coverage_signal=CoverageSignal.QUALITATIVELY_COVERED,
        follow_up_signal=FollowUpSignal.NONE
    )
    
    base_session.evaluation_history.append(er1)
    base_session.evaluation_history.append(er2)
    
    with pytest.raises(PersistenceInvariantError, match="Duplicate EvaluationRecord for QuestionRecord"):
        SessionPersistenceValidator.validate(base_session)
