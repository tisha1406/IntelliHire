from unittest.mock import AsyncMock, patch, MagicMock
import pytest
from datetime import datetime

from app.ai_interview.transport.services.interview_transport_service import InterviewTransportService
from app.ai_interview.transport.schemas.ws_commands import SubmitAnswerCommand
from app.ai_interview.transport.schemas.ws_events import EvaluationCompleteData
from app.ai_interview.answer_engine.schemas import EvaluationRecord
from app.ai_interview.answer_engine.enums import FollowUpSignal, CoverageSignal
from app.ai_interview.orchestration.interview_turn_coordinator import InterviewTurnResult
from app.ai_interview.question_engine.schemas import QuestionRecord
from app.ai_interview.schemas.session import InterviewSessionSchema, OperationClaim
from app.ai_interview.core.enums import InterviewState, QuestionType, DifficultyLevel
from app.ai_interview.question_engine.enums import QuestionStatus
from app.ai_interview.transport.websocket.authenticator import WsConnectionContext

@pytest.mark.asyncio
async def test_handle_submit_answer_evaluation_record_mapping():
    # Setup mocks
    repo = AsyncMock()
    coordinator = MagicMock()
    resume_repo = MagicMock()
    resume_repo.get_by_candidate = AsyncMock(return_value={"extracted_data": {"education": []}})
    mode_repo = MagicMock()
    mode_repo.get_by_mode_id = AsyncMock(return_value={
        "mode_id": "m1", "version": 1, "topic_budgets": [],
        "name": "m", "description": "d", "status": "published", "created_at": datetime.utcnow().isoformat()
    })
    
    svc = InterviewTransportService(
        session_repo=repo,
        coordinator=coordinator,
        resume_repo=resume_repo,
        mode_repo=mode_repo
    )
    
    # Fake session
    q_id = "test-q-id"
    session_id = "test-session"
    session = MagicMock(spec=InterviewSessionSchema)
    session.candidate_id = "cand-1"
    session.mode_id = "m1"
    session.mode_version = 1
    session.state = InterviewState.IN_PROGRESS
    session.version = 1
    session.questions_asked_total = 1
    session.completed_at = None
    session.question_history = [
        QuestionRecord(
            record_id=q_id,
            session_id=session_id,
            turn_number=1,
            topic_id="t1",
            question_text="Q",
            question_type=QuestionType.INITIAL,
            difficulty=DifficultyLevel.EASY,
            status=QuestionStatus.DISPATCHED
        )
    ]
    repo.get_by_id.return_value = session
    
    repo.claim_evaluation.return_value = OperationClaim(claim_id="eval-claim", claimed_at=datetime.utcnow(), expires_at=datetime.utcnow())
    repo.claim_question_generation.return_value = OperationClaim(claim_id="gen-claim", claimed_at=datetime.utcnow(), expires_at=datetime.utcnow())
    
    # Fake Coordinator Result
    eval_record = EvaluationRecord(
        evaluation_id="ev-1",
        question_record_id=q_id,
        topic_id="t1",
        overall_score=0.8,
        qualitative_coverage_signal=CoverageSignal.QUALITATIVELY_COVERED,
        follow_up_signal=FollowUpSignal.DEPTH_PROBE_MAY_HELP
    )
    
    from app.ai_interview.runtime.enums import RuntimeAction
    turn_result = InterviewTurnResult(
        action=RuntimeAction.NO_ACTION,
        evaluation=eval_record,
        interview_completed=False,
        waiting_for_answer=False,
        current_topic_id="t1",
        question=None
    )
    coordinator.advance_interview = MagicMock(return_value=turn_result)
    
    # Fake command
    command = SubmitAnswerCommand(
        command_type="submit_answer",
        command_id="cmd-1",
        session_id=session_id,
        payload={
            "question_record_id": q_id,
            "answer_text": "Here is my answer"
        }
    )
    
    context = WsConnectionContext(token=MagicMock(), session=session)
    
    # Mock event emitter
    with patch("app.ai_interview.transport.services.interview_transport_service.event_emitter", new_callable=AsyncMock) as mock_emitter, \
         patch("app.ai_interview.transport.services.interview_transport_service.get_interview_executor") as mock_executor, \
         patch("asyncio.get_event_loop") as mock_get_loop:
        
        # Make run_in_executor return the result directly
        mock_loop = AsyncMock()
        mock_loop.run_in_executor = AsyncMock(return_value=turn_result)
        mock_get_loop.return_value = mock_loop
        
        await svc.handle_submit_answer(session_id, command, context)
        
        # Verify emit_evaluation_complete was called with correct data
        mock_emitter.emit_evaluation_complete.assert_called_once()
        call_args = mock_emitter.emit_evaluation_complete.call_args
        
        assert call_args[0][0] == session_id
        eval_data: EvaluationCompleteData = call_args[0][1]
        
        assert eval_data.question_record_id == q_id
        assert eval_data.topic_id == "t1"
        assert eval_data.overall_score == 0.8
        assert eval_data.follow_up_signal == "depth_probe_may_help"
        assert eval_data.qualitative_coverage_signal == "qualitatively_covered"
        
        assert call_args.kwargs["correlation_id"] == "cmd-1"

@pytest.mark.asyncio
async def test_handle_submit_answer_interview_completed():
    # Setup mocks
    repo = AsyncMock()
    coordinator = MagicMock()
    resume_repo = MagicMock()
    resume_repo.get_by_candidate = AsyncMock(return_value={"extracted_data": {"education": []}})
    mode_repo = MagicMock()
    mode_repo.get_by_mode_id = AsyncMock(return_value={
        "mode_id": "m1", "version": 1, "topic_budgets": [],
        "name": "m", "description": "d", "status": "published", "created_at": datetime.utcnow().isoformat()
    })
    
    svc = InterviewTransportService(
        session_repo=repo,
        coordinator=coordinator,
        resume_repo=resume_repo,
        mode_repo=mode_repo
    )
    
    # Fake session
    q_id = "test-q-id"
    session_id = "test-session"
    session = MagicMock(spec=InterviewSessionSchema)
    session.candidate_id = "cand-1"
    session.mode_id = "m1"
    session.mode_version = 1
    session.state = InterviewState.IN_PROGRESS
    session.version = 1
    session.questions_asked_total = 1
    
    session.completed_at = datetime.utcnow()
    
    session.question_history = [
        QuestionRecord(
            record_id=q_id,
            session_id=session_id,
            turn_number=1,
            topic_id="t1",
            question_text="Q",
            question_type=QuestionType.INITIAL,
            difficulty=DifficultyLevel.EASY,
            status=QuestionStatus.DISPATCHED
        )
    ]
    repo.get_by_id.return_value = session
    
    repo.claim_evaluation.return_value = OperationClaim(claim_id="eval-claim", claimed_at=datetime.utcnow(), expires_at=datetime.utcnow())
    repo.claim_question_generation.return_value = OperationClaim(claim_id="gen-claim", claimed_at=datetime.utcnow(), expires_at=datetime.utcnow())
    
    # Fake Coordinator Result
    eval_record = EvaluationRecord(
        evaluation_id="ev-1",
        question_record_id=q_id,
        topic_id="t1",
        overall_score=0.9,
        qualitative_coverage_signal=CoverageSignal.QUALITATIVELY_COVERED,
        follow_up_signal=FollowUpSignal.NONE
    )
    
    from app.ai_interview.runtime.enums import RuntimeAction
    turn_result = InterviewTurnResult(
        action=RuntimeAction.COMPLETE,
        evaluation=eval_record,
        interview_completed=True,
        waiting_for_answer=False,
        current_topic_id="t1",
        question=None
    )
    coordinator.advance_interview = MagicMock(return_value=turn_result)
    
    command = SubmitAnswerCommand(
        command_type="submit_answer",
        command_id="cmd-2",
        session_id=session_id,
        payload={
            "question_record_id": q_id,
            "answer_text": "My final answer"
        }
    )
    
    context = WsConnectionContext(token=MagicMock(), session=session)
    
    with patch("app.ai_interview.transport.services.interview_transport_service.event_emitter", new_callable=AsyncMock) as mock_emitter, \
         patch("app.ai_interview.transport.services.interview_transport_service.get_interview_executor"), \
         patch("asyncio.get_event_loop") as mock_get_loop, \
         patch("app.services.interview_result_service.InterviewResultService") as mock_result_service_cls:
        
        mock_loop = AsyncMock()
        mock_loop.run_in_executor = AsyncMock(return_value=turn_result)
        mock_get_loop.return_value = mock_loop
        
        mock_result_service = AsyncMock()
        mock_result_service.generate_result_report.return_value = None
        mock_result_service_cls.return_value = mock_result_service
        
        await svc.handle_submit_answer(session_id, command, context)
        
        mock_emitter.emit_evaluation_complete.assert_called_once()
        call_args = mock_emitter.emit_evaluation_complete.call_args
        
        eval_data: EvaluationCompleteData = call_args[0][1]
        assert eval_data.topic_id == "t1"
        assert eval_data.overall_score == 0.9
        assert eval_data.follow_up_signal == "none"
        assert eval_data.qualitative_coverage_signal == "qualitatively_covered"

@pytest.mark.asyncio
async def test_handle_submit_answer_generation_failure():
    """
    Test that if advance_interview returns RuntimeAction.FAIL (e.g. LLM generator fails),
    handle_submit_answer executes a transition to FAILED, persists the failed state, 
    and emits an error, rather than falling through and keeping the session IN_PROGRESS.
    """
    repo = AsyncMock()
    coordinator = MagicMock()
    resume_repo = MagicMock()
    resume_repo.get_by_candidate = AsyncMock(return_value={"extracted_data": {"education": []}})
    mode_repo = MagicMock()
    mode_repo.get_by_mode_id = AsyncMock(return_value={
        "mode_id": "m1", "version": 1, "topic_budgets": [],
        "name": "m", "description": "d", "status": "published", "created_at": datetime.utcnow().isoformat()
    })
    
    svc = InterviewTransportService(
        session_repo=repo,
        coordinator=coordinator,
        resume_repo=resume_repo,
        mode_repo=mode_repo
    )
    
    q_id = "test-q-id"
    session_id = "test-session"
    session = MagicMock(spec=InterviewSessionSchema)
    session.candidate_id = "cand-1"
    session.mode_id = "m1"
    session.mode_version = 1
    session.state = InterviewState.IN_PROGRESS
    session.version = 1
    session.questions_asked_total = 1
    session.completed_at = None
    session.blueprint = MagicMock()
    session.blueprint.topics = []
    session.topic_progress = []
    session.question_history = [
        QuestionRecord(
            record_id=q_id,
            session_id=session_id,
            turn_number=1,
            topic_id="t1",
            question_text="Q",
            question_type=QuestionType.INITIAL,
            difficulty=DifficultyLevel.EASY,
            status=QuestionStatus.DISPATCHED
        )
    ]
    repo.get_by_id.return_value = session
    
    repo.claim_evaluation.return_value = OperationClaim(claim_id="eval-claim", claimed_at=datetime.utcnow(), expires_at=datetime.utcnow())
    repo.claim_question_generation.return_value = OperationClaim(claim_id="gen-claim", claimed_at=datetime.utcnow(), expires_at=datetime.utcnow())
    
    # Fake Coordinator Result with FAIL
    eval_record = EvaluationRecord(
        evaluation_id="ev-1",
        question_record_id=q_id,
        topic_id="t1",
        overall_score=0.8,
        qualitative_coverage_signal=CoverageSignal.QUALITATIVELY_COVERED,
        follow_up_signal=FollowUpSignal.NONE
    )
    
    from app.ai_interview.runtime.enums import RuntimeAction
    turn_result = InterviewTurnResult(
        action=RuntimeAction.FAIL,
        evaluation=eval_record,
        interview_completed=False,
        waiting_for_answer=False,
        current_topic_id="t1",
        question=None
    )
    coordinator.advance_interview = MagicMock(return_value=turn_result)
    
    command = SubmitAnswerCommand(
        command_type="submit_answer",
        command_id="cmd-fail",
        session_id=session_id,
        payload={
            "question_record_id": q_id,
            "answer_text": "Answer"
        }
    )
    
    context = WsConnectionContext(token=MagicMock(), session=session)
    
    with patch("app.ai_interview.transport.services.interview_transport_service.event_emitter", new_callable=AsyncMock) as mock_emitter, \
         patch("app.ai_interview.transport.services.interview_transport_service.get_interview_executor"), \
         patch("asyncio.get_event_loop") as mock_get_loop:
        
        mock_loop = AsyncMock()
        mock_loop.run_in_executor = AsyncMock(return_value=turn_result)
        mock_get_loop.return_value = mock_loop
        
        await svc.handle_submit_answer(session_id, command, context)
        
        # 1. State machine transitioned to FAILED
        assert session.state == InterviewState.FAILED
        
        # 2. Persisted failed state
        repo.save.assert_called_with(
            session,
            expected_version=session.version,
            evaluation_fencing_id="eval-claim",
            generation_fencing_id="gen-claim"
        )
        
        # 3. Error event emitted (GENERATION_FAILED)
        mock_emitter.emit_error.assert_called_once()
        error_payload = mock_emitter.emit_error.call_args[0][1]
        assert error_payload.code == "GENERATION_FAILED"
        
        # 4. No next_question_ready emitted
        mock_emitter.emit_next_question_ready.assert_not_called()
        
        # 5. Normal evaluation complete is NOT emitted (session fails immediately)
        mock_emitter.emit_evaluation_complete.assert_not_called()

@pytest.mark.asyncio
async def test_handle_submit_answer_practice_completion():
    repo = AsyncMock()
    coordinator = MagicMock()
    resume_repo = MagicMock()
    resume_repo.get_by_candidate = AsyncMock(return_value={"extracted_data": {"education": []}})
    mode_repo = MagicMock()
    mode_repo.get_by_mode_id = AsyncMock(return_value={
        "mode_id": "practice", "version": 1, "topic_budgets": [],
        "name": "p", "description": "d", "status": "published", "created_at": datetime.utcnow().isoformat()
    })
    
    svc = InterviewTransportService(
        session_repo=repo,
        coordinator=coordinator,
        resume_repo=resume_repo,
        mode_repo=mode_repo
    )
    
    q_id = "test-q-id"
    session_id = "test-session"
    session = MagicMock(spec=InterviewSessionSchema)
    session.candidate_id = "cand-1"
    session.mode_id = "practice"
    session.mode_version = 1
    session.state = InterviewState.IN_PROGRESS
    session.version = 1
    session.questions_asked_total = 1
    session.completed_at = datetime.utcnow()
    
    session.question_history = [
        QuestionRecord(
            record_id=q_id,
            session_id=session_id,
            turn_number=1,
            topic_id="t1",
            question_text="Q",
            question_type=QuestionType.INITIAL,
            difficulty=DifficultyLevel.EASY,
            status=QuestionStatus.DISPATCHED
        )
    ]
    repo.get_by_id.return_value = session
    
    repo.claim_evaluation.return_value = OperationClaim(claim_id="eval-claim", claimed_at=datetime.utcnow(), expires_at=datetime.utcnow())
    repo.claim_question_generation.return_value = OperationClaim(claim_id="gen-claim", claimed_at=datetime.utcnow(), expires_at=datetime.utcnow())
    
    eval_record = EvaluationRecord(
        evaluation_id="ev-1",
        question_record_id=q_id,
        topic_id="t1",
        overall_score=0.9,
        qualitative_coverage_signal=CoverageSignal.QUALITATIVELY_COVERED,
        follow_up_signal=FollowUpSignal.NONE
    )
    
    from app.ai_interview.runtime.enums import RuntimeAction
    turn_result = InterviewTurnResult(
        action=RuntimeAction.COMPLETE,
        evaluation=eval_record,
        interview_completed=True,
        waiting_for_answer=False,
        current_topic_id="t1",
        question=None
    )
    coordinator.advance_interview = MagicMock(return_value=turn_result)
    
    command = SubmitAnswerCommand(
        command_type="submit_answer",
        command_id="cmd-2",
        session_id=session_id,
        payload={
            "question_record_id": q_id,
            "answer_text": "My practice answer"
        }
    )
    
    context = WsConnectionContext(token=MagicMock(), session=session)
    
    with patch("app.ai_interview.transport.services.interview_transport_service.event_emitter", new_callable=AsyncMock) as mock_emitter, \
         patch("app.ai_interview.transport.services.interview_transport_service.get_interview_executor"), \
         patch("asyncio.get_event_loop") as mock_get_loop, \
         patch("app.services.interview_result_service.InterviewResultService") as mock_result_service_cls, \
         patch("app.services.candidate_portal_service.CandidatePortalService") as mock_portal_service_cls:
        
        mock_loop = AsyncMock()
        mock_loop.run_in_executor = AsyncMock(return_value=turn_result)
        mock_get_loop.return_value = mock_loop
        
        mock_portal_service = AsyncMock()
        mock_portal_service_cls.return_value = mock_portal_service
        
        await svc.handle_submit_answer(session_id, command, context)
        
        mock_result_service_cls.assert_not_called()
        mock_portal_service.complete_practice.assert_called_once_with("cand-1")

