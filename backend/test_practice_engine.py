import asyncio
import json
from bson import ObjectId
from app.db.mongo import get_database
from app.ai_interview.transport.services.session_creation_service import SessionCreationService
from app.auth.jwt_handler import TokenPayload
from app.repositories.candidate_repository import CandidateRepository
from app.repositories.campaign_repository import CampaignRepository
from app.ai_interview.persistence.repository import InterviewSessionRepository
from app.repositories.resume_repository import ResumeRepository
from app.repositories.interview_mode_repository import InterviewModeRepository
from app.ai_interview.orchestration.interview_turn_coordinator import InterviewTurnCoordinator
from app.ai_interview.question_engine.question_engine import QuestionEngine
from app.ai_interview.answer_engine.answer_engine import AnswerEngine
from app.ai_interview.llm_infrastructure.adapters.openai_adapter import OpenAICompatibleAdapter
from app.ai_interview.question_engine.llm_question_generator import LLMQuestionGenerator
from app.ai_interview.answer_engine.llm_answer_evaluator import LLMAnswerEvaluator
from app.ai_interview.transport.services.interview_transport_service import InterviewTransportService
from app.ai_interview.transport.schemas.ws_commands import StartInterviewCommand
from app.ai_interview.transport.websocket.authenticator import WsConnectionContext

async def main():
    from app.db.mongo import connect_db
    from app.ai_interview.transport import set_interview_executor
    from concurrent.futures import ThreadPoolExecutor
    
    set_interview_executor(ThreadPoolExecutor(max_workers=2))
    await connect_db()
    db = get_database()
    campaign_repo = CampaignRepository()
    candidate_repo = CandidateRepository()
    session_repo = InterviewSessionRepository(db.interview_sessions)
    resume_repo = ResumeRepository()
    mode_repo = InterviewModeRepository()
    
    # Get any active candidate
    cand_doc = await db.candidates.find_one({})
    candidate_id = str(cand_doc["_id"])
    company_id = str(cand_doc.get("company_id", "6a749346ba2af4d02d21e4a1"))
    
    import time
    now = int(time.time())
    token = TokenPayload(
        sub="mock_user",
        user_id="mock_user",
        email="test@test.com",
        role="candidate",
        candidate_id=candidate_id,
        company_id=company_id,
        iat=now,
        exp=now + 3600
    )
    
    # 1. Create Practice Session
    service = SessionCreationService(
        campaign_repo=campaign_repo,
        mode_repo=mode_repo,
        resume_repo=resume_repo,
        candidate_repo=candidate_repo,
        session_repo=session_repo
    )
    candidate = await candidate_repo.get(candidate_id)
    campaign_id = str(candidate.get("campaign_id")) if candidate and candidate.get("campaign_id") else None
    
    session_data = await service.create_session(token, campaign_id, is_practice=True)
    session_id = session_data["session_id"]
    print("Created session:", session_id)
    
    # 2. Simulate start_interview via Transport Service
    llm_provider = OpenAICompatibleAdapter()
    transport = InterviewTransportService(
        session_repo=session_repo,
        resume_repo=resume_repo,
        mode_repo=mode_repo,
        coordinator=InterviewTurnCoordinator(
            question_engine=QuestionEngine(generator=LLMQuestionGenerator(llm_provider)),
            answer_engine=AnswerEngine(evaluator=LLMAnswerEvaluator(llm_provider))
        )
    )
    
    session = await session_repo.get_by_id(session_id)
    context = WsConnectionContext(
        token=token,
        session=session
    )
    
    cmd = StartInterviewCommand(command_type="start_interview", command_id="cmd-123")
    
    print("Executing start_interview...")
    await transport.handle_start_interview(session_id, cmd, context)
    print("Done!")

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv(".env")
    asyncio.run(main())
