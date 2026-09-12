from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import logging
from typing import Optional

from app.db.mongo import get_database
from app.ai_interview.persistence.repository import InterviewSessionRepository
from app.ai_interview.transport.websocket.authenticator import authenticate_ws, WsConnectionContext
from app.ai_interview.transport.websocket.connection_manager import connection_manager
from app.ai_interview.transport.websocket.command_router import command_router
from app.ai_interview.transport.websocket.event_emitter import event_emitter
from app.ai_interview.transport.exceptions import WsCommandError
from app.ai_interview.transport.schemas.ws_commands import WsCommandBase
from app.ai_interview.transport.schemas.ws_errors import build_error_payload, WsErrorCode

from app.repositories.resume_repository import ResumeRepository
from app.repositories.interview_mode_repository import InterviewModeRepository
from app.ai_interview.transport.services.interview_transport_service import InterviewTransportService
from app.ai_interview.orchestration.interview_turn_coordinator import InterviewTurnCoordinator
from app.ai_interview.question_engine.question_engine import QuestionEngine
from app.ai_interview.answer_engine.answer_engine import AnswerEngine

from app.ai_interview.llm_infrastructure.adapters.openai_adapter import OpenAICompatibleAdapter
from app.ai_interview.question_engine.llm_question_generator import LLMQuestionGenerator
from app.ai_interview.answer_engine.llm_answer_evaluator import LLMAnswerEvaluator

logger = logging.getLogger("intellihire")

router = APIRouter(
    prefix="/ws",
    tags=["WebSocket"],
)

def get_transport_service() -> InterviewTransportService:
    db = get_database()
    llm_provider = OpenAICompatibleAdapter()
    return InterviewTransportService(
        session_repo=InterviewSessionRepository(db.interview_sessions),
        resume_repo=ResumeRepository(),
        mode_repo=InterviewModeRepository(),
        coordinator=InterviewTurnCoordinator(
            question_engine=QuestionEngine(generator=LLMQuestionGenerator(llm_provider)),
            answer_engine=AnswerEngine(evaluator=LLMAnswerEvaluator(llm_provider))
        )
    )

@router.websocket("/interview/{session_id}")
async def interview_websocket(
    websocket: WebSocket,
    session_id: str,
):
    """
    Phase 9 — Live Interview WebSocket Endpoint
    """
    # 1. Authenticate (before accept)
    db = get_database()
    repo = InterviewSessionRepository(db.interview_sessions)
    context: Optional[WsConnectionContext] = await authenticate_ws(websocket, session_id, repo)
    
    if not context:
        # authenticate_ws already called websocket.close()
        return

    # 2. Accept and Register
    await websocket.accept()
    await connection_manager.register(session_id, websocket)
    
    # 3. Handle Reconnect / Recovery
    transport_service = get_transport_service()
    try:
        await transport_service.handle_reconnect(session_id, context)
    except Exception as e:
        logger.exception("Failed to handle reconnect")
        await websocket.close(code=1011, reason="Internal error during recovery")
        connection_manager.remove(session_id)
        return

    # 4. Command Loop
    try:
        while True:
            raw_text = await websocket.receive_text()
            
            try:
                command: WsCommandBase = command_router.parse(session_id, raw_text)
                
                if command.command_type == "start_interview":
                    await transport_service.handle_start_interview(session_id, command, context)
                elif command.command_type == "submit_answer":
                    await transport_service.handle_submit_answer(session_id, command, context)
                elif command.command_type == "pause_interview":
                    await transport_service.handle_pause(session_id, command, context)
                elif command.command_type == "resume_interview":
                    await transport_service.handle_resume(session_id, command, context)
                elif command.command_type == "ping":
                    await event_emitter.emit_pong(session_id, correlation_id=command.command_id)
                    
            except WsCommandError as ce:
                # E.g. Payload too large, invalid JSON, invalid schema, deduplication hit
                code = WsErrorCode.INVALID_COMMAND
                if type(ce).__name__ == "WsPayloadTooLargeError":
                    code = WsErrorCode.PAYLOAD_TOO_LARGE
                elif type(ce).__name__ == "WsDuplicateCommandError":
                    code = WsErrorCode.DUPLICATE_COMMAND
                    
                payload = build_error_payload(code, override_message=str(ce))
                await event_emitter.emit_error(session_id, payload)
                
            except Exception as e:
                logger.exception(f"Unhandled error processing WS command for session {session_id}")
                payload = build_error_payload(WsErrorCode.INTERNAL_ERROR)
                await event_emitter.emit_error(session_id, payload)

    except (WebSocketDisconnect, RuntimeError):
        # Disconnect is safe; state remains IN_PROGRESS in MongoDB
        # RuntimeError is thrown by Starlette/AnyIO if the socket is closed while waiting to receive (e.g. replaced)
        logger.info({"event": "ws_disconnect", "session_id": session_id})
        connection_manager.remove(session_id)
        command_router.cleanup_session(session_id)