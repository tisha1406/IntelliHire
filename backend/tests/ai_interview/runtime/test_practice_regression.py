import pytest
from unittest.mock import MagicMock, AsyncMock, patch
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
from app.ai_interview.question_engine.schemas import GeneratedQuestion

@pytest.mark.asyncio
async def test_practice_mode_regression():
    # 1. Setup mocks
    candidate_repo = AsyncMock()
    candidate_repo.get.return_value = {"_id": "cand_1", "campaign_id": "camp_1"}
    
    # We need a real-ish session repo to persist state across calls
    class MockSessionRepo:
        def __init__(self):
            self.sessions = {}
        async def get_by_id(self, session_id):
            return self.sessions.get(session_id)
        async def create(self, session):
            self.sessions[session.session_id] = session
        async def save(self, session, **kwargs):
            self.sessions[session.session_id] = session
            session.version += 1
            return session
        async def find_active_session(self, *args, **kwargs):
            return None
        async def claim_question_generation(self, session_id, **kwargs):
            return MagicMock(claim_id="gen-claim")
        async def release_question_generation(self, *args, **kwargs):
            pass
        async def claim_evaluation(self, *args, **kwargs):
            return MagicMock(claim_id="eval-claim")
        async def release_evaluation(self, *args, **kwargs):
            pass
            
    session_repo = MockSessionRepo()
    
    mock_mode_repo = AsyncMock()
    mock_mode_repo.get_by_mode_id.return_value = {"mode_id": "practice", "version": 1, "topic_budgets": []}
    
    # Mocks for engines to ensure they are NOT called for practice
    llm_generator = AsyncMock()
    llm_generator.generate.side_effect = Exception("LLM should not be called in practice mode!")
    
    llm_evaluator = AsyncMock()
    llm_evaluator.evaluate.side_effect = Exception("Evaluator should not be called in practice mode!")
    
    q_engine = QuestionEngine(generator=llm_generator)
    a_engine = AnswerEngine(evaluator=llm_evaluator)
    coordinator = InterviewTurnCoordinator(q_engine, a_engine)
    
    # Emitting events
    event_emitter = AsyncMock()
    
    with patch("app.ai_interview.transport.services.interview_transport_service.event_emitter", event_emitter), \
         patch("app.ai_interview.transport.services.interview_transport_service.get_interview_executor") as mock_exec:
         
        # Execute run_in_executor synchronously for tests
        import asyncio
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
            
            assert session_data["mode_id"] == "practice"
            
            session = await session_repo.get_by_id(session_id)
            assert session.state == InterviewState.CREATED
            assert len(session.blueprint.topics) == 3
            assert session.blueprint.topics[0].topic_id == "practice_1"
            assert session.blueprint.topics[1].topic_id == "practice_2"
            assert session.blueprint.topics[2].topic_id == "practice_3"
            
            transport = InterviewTransportService(
                session_repo=session_repo,
                resume_repo=AsyncMock(),
                mode_repo=mock_mode_repo,
                coordinator=coordinator
            )
            context = WsConnectionContext(token=token, session=session)
            
            # Q1
            await transport.handle_start_interview(session_id, StartInterviewCommand(command_type="start_interview", command_id="c1"), context)
            
            session = await session_repo.get_by_id(session_id)
            assert session.state == InterviewState.IN_PROGRESS
            assert len(session.question_history) == 1
            assert session.question_history[0].topic_id == "practice_1"
            assert session.question_history[0].question_text == "Tell me about yourself."
            
            # Submit Q1 Answer
            await transport.handle_submit_answer(session_id, SubmitAnswerCommand(command_type="submit_answer", command_id="c2", payload={"question_record_id": session.question_history[0].record_id, "answer_text": "A1"}), context)
            
            session = await session_repo.get_by_id(session_id)
            assert session.question_history[0].status == QuestionStatus.EVALUATED
            assert len(session.question_history) == 2
            assert session.question_history[1].topic_id == "practice_2"
            assert session.question_history[1].question_text == "What is the last project you worked on?"
            
            # Submit Q2 Answer
            await transport.handle_submit_answer(session_id, SubmitAnswerCommand(command_type="submit_answer", command_id="c3", payload={"question_record_id": session.question_history[1].record_id, "answer_text": "A2"}), context)
            
            session = await session_repo.get_by_id(session_id)
            assert session.question_history[1].status == QuestionStatus.EVALUATED
            assert len(session.question_history) == 3
            assert session.question_history[2].topic_id == "practice_3"
            assert session.question_history[2].question_text == "What role or area are you specifically strongest in?"
            
            # Submit Q3 Answer
            await transport.handle_submit_answer(session_id, SubmitAnswerCommand(command_type="submit_answer", command_id="c4", payload={"question_record_id": session.question_history[2].record_id, "answer_text": "A3"}), context)
            
            session = await session_repo.get_by_id(session_id)
            assert session.question_history[2].status == QuestionStatus.EVALUATED
            assert session.state == InterviewState.COMPLETED
            
            # Verify no LLM was called
            llm_generator.generate.assert_not_called()
            llm_evaluator.evaluate.assert_not_called()
