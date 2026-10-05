import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timezone

from app.ai_interview.transport.services.interview_transport_service import InterviewTransportService
from app.ai_interview.schemas.session import InterviewSessionSchema, TopicProgress
from app.ai_interview.question_engine.schemas import QuestionRecord
from app.ai_interview.core.enums import InterviewState, QuestionType, DifficultyLevel
from app.ai_interview.question_engine.enums import QuestionStatus
from app.ai_interview.transport.schemas.ws_commands import (
    StartInterviewCommand, SubmitAnswerCommand, SubmitAnswerPayload
)
from app.ai_interview.transport.websocket.authenticator import WsConnectionContext
from app.ai_interview.persistence.repository import OperationClaim
from app.ai_interview.schemas.blueprint import InterviewBlueprint, TopicBlueprint
from app.ai_interview.schemas.interview_mode import InterviewModeDefinition
from app.ai_interview.orchestration.schemas import InterviewTurnResult
from app.ai_interview.runtime.schemas import RuntimeAction

@pytest.fixture
def mock_context():
    return MagicMock()

@pytest.fixture
def mock_repo():
    repo = AsyncMock()
    # Mock save to just do nothing so we can inspect the session object
    repo.save = AsyncMock()
    return repo

@pytest.fixture
def mock_coordinator():
    coord = MagicMock()
    return coord

@pytest.fixture
def service(mock_repo, mock_coordinator):
    svc = InterviewTransportService(
        session_repo=mock_repo,
        resume_repo=AsyncMock(),
        mode_repo=AsyncMock(),
        coordinator=mock_coordinator
    )
    svc._load_candidate_context = AsyncMock(return_value={})
    svc._load_mode = AsyncMock(return_value=InterviewModeDefinition(
        mode_id="m1", version=1, name="Mode", description="Test", status="published", created_at=datetime.now(timezone.utc), settings={}
    ))
    return svc

@pytest.mark.asyncio
@patch("app.ai_interview.transport.services.interview_transport_service.event_emitter")
@patch("app.ai_interview.transport.services.interview_transport_service.get_interview_executor")
async def test_start_interview_claim_cleanup(mock_executor, mock_emitter, service, mock_repo, mock_context):
    # Setup session
    session = InterviewSessionSchema(
        session_id="s1",
        candidate_id="cand1",
        company_id="comp1",
        campaign_id="camp1",
        mode_id="m1",
        mode_version=1,
        created_at=datetime.now(timezone.utc),
        state=InterviewState.CREATED,
        version=1,
        question_history=[],
        blueprint=InterviewBlueprint(mode_id="m1", blueprint_version="1", min_questions=1, max_questions=5, total_question_budget=5, emergency_max_questions=10, topics=[
            TopicBlueprint(topic_id="t1", topic_name="T1", source="resume", priority=1, mandatory=True, question_budget=2)
        ])
    )
    
    # Mock claim acquired
    gen_claim = OperationClaim(claim_id="gen1", claimed_at=datetime.now(timezone.utc), expires_at=datetime.now(timezone.utc))
    
    # Sequence of repo.get_by_id:
    # 1. At start
    # 2. After claim is acquired (the db would have the claim)
    session_with_claim = session.model_copy(deep=True)
    session_with_claim.generation_claim = gen_claim
    
    mock_repo.get_by_id.side_effect = [session, session_with_claim]
    mock_repo.claim_question_generation.return_value = gen_claim
    
    # Mock engine result
    qr = QuestionRecord(session_id="s1", turn_number=1, record_id="q1", topic_id="t1", question_text="q", status=QuestionStatus.DISPATCHED, question_type="initial", difficulty="medium")
    mock_executor.return_value = None # not actually used because we patch run_in_executor
    
    # Patch asyncio.get_event_loop().run_in_executor
    with patch.object(asyncio.get_event_loop(), "run_in_executor") as mock_run:
        future = asyncio.Future()
        future.set_result(InterviewTurnResult(
            action=RuntimeAction.NO_ACTION, # not used
            question=qr,
            evaluation=None,
            interview_completed=False,
            waiting_for_answer=True,
            current_topic_id="t1"
        ))
        mock_run.return_value = future
        mock_emitter.emit_question_generating = AsyncMock()
        mock_emitter.emit_interview_started = AsyncMock()
        mock_emitter.emit_question_ready = AsyncMock()
        
        command = StartInterviewCommand(command_id="cmd1", command_type="start_interview")
        await service.handle_start_interview("s1", command, mock_context)
        
        # Verify save was called
        assert mock_repo.save.called
        
        # Verify claim was cleared before save
        saved_session = mock_repo.save.call_args[0][0]
        assert saved_session.generation_claim is None
        
        # Verify fencing id was passed
        kwargs = mock_repo.save.call_args[1]
        assert kwargs["generation_fencing_id"] == "gen1"

@pytest.mark.asyncio
@patch("app.ai_interview.transport.services.interview_transport_service.event_emitter")
@patch("app.ai_interview.transport.services.interview_transport_service.get_interview_executor")
async def test_submit_answer_claim_cleanup(mock_executor, mock_emitter, service, mock_repo, mock_context):
    qr = QuestionRecord(
        session_id="s1", turn_number=1, record_id="q1", topic_id="t1", 
        question_text="q", status=QuestionStatus.DISPATCHED, question_type="initial", difficulty="medium"
    )
    
    session = InterviewSessionSchema(
        session_id="s1",
        candidate_id="cand1",
        company_id="comp1",
        campaign_id="camp1",
        mode_id="m1",
        mode_version=1,
        created_at=datetime.now(timezone.utc),
        state=InterviewState.IN_PROGRESS,
        version=1,
        question_history=[qr],
        blueprint=InterviewBlueprint(mode_id="m1", blueprint_version="1", min_questions=1, max_questions=5, total_question_budget=5, emergency_max_questions=10, topics=[])
    )
    
    eval_claim = OperationClaim(claim_id="ev1", claimed_at=datetime.now(timezone.utc), expires_at=datetime.now(timezone.utc))
    gen_claim = OperationClaim(claim_id="gen1", claimed_at=datetime.now(timezone.utc), expires_at=datetime.now(timezone.utc))
    
    session_with_claims = session.model_copy(deep=True)
    session_with_claims.question_history[0].evaluation_claim = eval_claim
    session_with_claims.generation_claim = gen_claim
    
    mock_repo.get_by_id.side_effect = [session, session_with_claims]
    mock_repo.claim_evaluation.return_value = eval_claim
    mock_repo.claim_question_generation.return_value = gen_claim
    
    qr2 = QuestionRecord(session_id="s1", turn_number=2, record_id="q2", topic_id="t1", question_text="q2", status=QuestionStatus.DISPATCHED, question_type="initial", difficulty="medium")
    
    with patch.object(asyncio.get_event_loop(), "run_in_executor") as mock_run:
        future = asyncio.Future()
        future.set_result(InterviewTurnResult(
            action=RuntimeAction.NO_ACTION,
            question=qr2,
            evaluation=None,
            interview_completed=False,
            waiting_for_answer=True,
            current_topic_id="t1"
        ))
        mock_run.return_value = future
        mock_emitter.emit_answer_received = AsyncMock()
        mock_emitter.emit_evaluation_processing = AsyncMock()
        mock_emitter.emit_evaluation_complete = AsyncMock()
        mock_emitter.emit_decision_ready = AsyncMock()
        mock_emitter.emit_question_ready = AsyncMock()
        mock_emitter.emit_next_question_ready = AsyncMock()
        
        command = SubmitAnswerCommand(command_id="cmd2", command_type="submit_answer", payload=SubmitAnswerPayload(question_record_id="q1", answer_text="ans"))
        await service.handle_submit_answer("s1", command, mock_context)
        
        assert mock_repo.save.called
        saved_session = mock_repo.save.call_args[0][0]
        
        # Claims must be cleared before save
        assert saved_session.generation_claim is None
        assert saved_session.question_history[0].evaluation_claim is None
        
        kwargs = mock_repo.save.call_args[1]
        assert kwargs["evaluation_fencing_id"] == "ev1"
        assert kwargs["generation_fencing_id"] == "gen1"
