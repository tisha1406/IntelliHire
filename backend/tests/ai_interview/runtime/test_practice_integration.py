import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime, timezone
import os

from app.db.mongo import connect_db, get_database, client
from app.ai_interview.persistence.repository import InterviewSessionRepository
from app.ai_interview.persistence.exceptions import ClaimAlreadyHeldError
from app.ai_interview.transport.services.session_creation_service import SessionCreationService
from app.ai_interview.transport.services.interview_transport_service import InterviewTransportService
from app.ai_interview.orchestration.interview_turn_coordinator import InterviewTurnCoordinator
from app.ai_interview.question_engine.question_engine import QuestionEngine
from app.ai_interview.answer_engine.answer_engine import AnswerEngine
from app.ai_interview.transport.schemas.ws_commands import StartInterviewCommand, SubmitAnswerCommand
from app.ai_interview.transport.websocket.authenticator import WsConnectionContext
from app.ai_interview.core.enums import InterviewState
from app.ai_interview.question_engine.enums import QuestionStatus
from app.auth.jwt_handler import TokenPayload

import pytest_asyncio

@pytest.fixture(scope="module")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest_asyncio.fixture(scope="module", autouse=True)
async def setup_test_db():
    os.environ["DATABASE_NAME"] = "intellihire_test"
    await connect_db()
    db = get_database()
    yield db
    if client:
        client.close()

@pytest.mark.asyncio
async def test_practice_mode_real_persistence(setup_test_db):
    db = setup_test_db
    
    # 0. STRICT ISOLATION ASSERTION
    assert db.name == "intellihire_test", "CRITICAL: Test is NOT using the isolated test database!"
    
    # Clear sessions for test
    await db.interview_sessions.delete_many({})
    
    session_repo = InterviewSessionRepository(db.interview_sessions)
    
    candidate_repo = AsyncMock()
    candidate_repo.get.return_value = {"_id": "cand_1", "campaign_id": "camp_1"}
    
    mock_mode_repo = AsyncMock()
    mock_mode_repo.get_by_mode_id.return_value = {"mode_id": "practice", "version": 1, "topic_budgets": []}
    
    # Mock LLM out
    llm_generator = AsyncMock()
    llm_generator.generate.side_effect = Exception("LLM MUST NOT BE CALLED IN PRACTICE MODE")
    llm_evaluator = AsyncMock()
    llm_evaluator.evaluate.side_effect = Exception("Evaluator MUST NOT BE CALLED IN PRACTICE MODE")
    
    q_engine = QuestionEngine(generator=llm_generator)
    a_engine = AnswerEngine(evaluator=llm_evaluator)
    coordinator = InterviewTurnCoordinator(q_engine, a_engine)
    
    event_emitter = AsyncMock()
    
    with patch("app.ai_interview.transport.services.interview_transport_service.event_emitter", event_emitter), \
         patch("app.ai_interview.transport.services.interview_transport_service.get_interview_executor") as mock_exec, \
         patch("app.ai_interview.blueprint_planning.planner.InterviewBlueprintPlanner.plan", side_effect=Exception("Planner MUST NOT BE CALLED IN PRACTICE MODE")), \
         patch("app.ai_interview.runtime.shadow_priority_calculator.ShadowPriorityCalculator.calculate_priority", side_effect=Exception("ShadowPriorityCalculator MUST NOT BE CALLED IN PRACTICE MODE")):
         
        # Execute run_in_executor synchronously
        mock_exec.return_value = None
        loop = asyncio.get_event_loop()
        
        async def mock_run_in_executor(executor, func, *args, **kwargs):
            import inspect
            if inspect.iscoroutinefunction(func):
                return await func(*args, **kwargs)
            return func(*args, **kwargs)
            
        with patch.object(loop, 'run_in_executor', new=mock_run_in_executor):
            # Session Creation
            mock_campaign_repo = AsyncMock()
            mock_campaign_repo.get_by_id.return_value = {}
            mock_resume_repo = AsyncMock()
            mock_resume_repo.get_by_candidate.return_value = {}
            
            creation_service = SessionCreationService(
                campaign_repo=mock_campaign_repo,
                mode_repo=mock_mode_repo,
                resume_repo=mock_resume_repo,
                candidate_repo=candidate_repo,
                session_repo=session_repo
            )
            
            import time
            now = int(time.time())
            token = TokenPayload(candidate_id="cand_1", company_id="comp_1", role="candidate", sub="sub", user_id="user", iat=now, exp=now+3600)
            
            session_data = await creation_service.create_session(token, "camp_1", is_practice=True)
            session_id = session_data["session_id"]
            
            transport = InterviewTransportService(
                session_repo=session_repo,
                resume_repo=mock_resume_repo,
                mode_repo=mock_mode_repo,
                coordinator=coordinator
            )
            context = WsConnectionContext(token=token, session=await session_repo.get_by_id(session_id))
            
            # 1. Start Interview (Q1)
            await transport.handle_start_interview(session_id, StartInterviewCommand(command_type="start_interview", command_id="c1"), context)
            
            session = await session_repo.get_by_id(session_id)
            assert session.mode_id == "practice"
            assert session.state == InterviewState.IN_PROGRESS
            assert session.generation_claim is None # Proves claim was successfully released during persistence
            
            # 2. Q1 -> Q2
            cmd2 = SubmitAnswerCommand(command_type="submit_answer", command_id="c2", payload={"question_record_id": session.question_history[0].record_id, "answer_text": "A1"})
            await transport.handle_submit_answer(session_id, cmd2, context)
            
            session = await session_repo.get_by_id(session_id)
            assert session.question_history[0].status == QuestionStatus.EVALUATED
            assert len(session.question_history) == 2
            assert session.generation_claim is None # Proves claim was successfully released during persistence
            
            # 2a. Duplicate submission for Q1 should fail gracefully via idempotency
            await transport.handle_submit_answer(session_id, cmd2, context)
            session_duplicate = await session_repo.get_by_id(session_id)
            assert len(session_duplicate.question_history) == 2 # Did not generate Q3
            assert session_duplicate.version == session.version # No DB change
            
            # 3. Q2 -> Q3
            cmd3 = SubmitAnswerCommand(command_type="submit_answer", command_id="c3", payload={"question_record_id": session.question_history[1].record_id, "answer_text": "A2"})
            await transport.handle_submit_answer(session_id, cmd3, context)
            
            session = await session_repo.get_by_id(session_id)
            assert len(session.question_history) == 3
            assert session.generation_claim is None
            
            # 3a. Test Disconnect/Reconnect Simulation
            await transport.handle_reconnect(session_id, context)
            event_emitter.emit_session_snapshot.assert_called()
            
            session_reconnect = await session_repo.get_by_id(session_id)
            assert len(session_reconnect.question_history) == 3 # Still exactly 3, didn't create a new one
            assert session_reconnect.question_history[-1].status == QuestionStatus.DISPATCHED
            
            # 4. Q3 -> Completion
            cmd4 = SubmitAnswerCommand(command_type="submit_answer", command_id="c4", payload={"question_record_id": session.question_history[2].record_id, "answer_text": "A3"})
            await transport.handle_submit_answer(session_id, cmd4, context)
            
            session = await session_repo.get_by_id(session_id)
            assert session.state == InterviewState.COMPLETED
            assert session.generation_claim is None
