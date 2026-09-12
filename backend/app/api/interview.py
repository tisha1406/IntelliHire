from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)

from app.auth.jwt_handler import TokenPayload, decode_jwt
from app.rbac.permissions import require_role
from app.rbac.models import UserRole

from app.schemas.interview import (
    CreateSessionRequest,
    CreateSessionResponse,
)
from app.ai_interview.transport.schemas.ws_events import SessionSnapshotData

# Services & Repositories
from app.repositories.campaign_repository import CampaignRepository
from app.repositories.interview_mode_repository import InterviewModeRepository
from app.repositories.resume_repository import ResumeRepository
from app.repositories.candidate_repository import CandidateRepository
from app.ai_interview.persistence.repository import InterviewSessionRepository
from app.db.mongo import get_database

from app.ai_interview.transport.services.session_creation_service import SessionCreationService
from app.ai_interview.transport.services.interview_transport_service import InterviewTransportService
from app.ai_interview.orchestration.interview_turn_coordinator import InterviewTurnCoordinator
from app.ai_interview.question_engine.question_engine import QuestionEngine
from app.ai_interview.answer_engine.answer_engine import AnswerEngine

from app.ai_interview.llm_infrastructure.adapters.openai_adapter import OpenAICompatibleAdapter
from app.ai_interview.question_engine.llm_question_generator import LLMQuestionGenerator
from app.ai_interview.answer_engine.llm_answer_evaluator import LLMAnswerEvaluator

router = APIRouter(
    prefix="/api/interview",
    tags=["Interview"],
)

def get_session_creation_service() -> SessionCreationService:
    db = get_database()
    return SessionCreationService(
        campaign_repo=CampaignRepository(),
        mode_repo=InterviewModeRepository(),
        resume_repo=ResumeRepository(),
        candidate_repo=CandidateRepository(),
        session_repo=InterviewSessionRepository(db.interview_sessions)
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

@router.post(
    "/campaigns/{campaign_id}/sessions",
    response_model=CreateSessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Interview Session",
)
async def create_session(
    campaign_id: str,
    request: CreateSessionRequest,
    token: TokenPayload = Depends(require_role(UserRole.CANDIDATE)),
    service: SessionCreationService = Depends(get_session_creation_service)
):
    """
    Creates a new deterministic InterviewSession for a candidate.
    """
    if not token.candidate_id:
        raise HTTPException(status_code=403, detail="Not a valid candidate token")
        
    result = await service.create_session(token, campaign_id)
    return CreateSessionResponse(**result)


@router.get(
    "/sessions/{session_id}",
    response_model=SessionSnapshotData,
    summary="Get Session Snapshot",
)
async def get_session_snapshot(
    session_id: str,
    token: TokenPayload = Depends(require_role(UserRole.CANDIDATE)),
    service: InterviewTransportService = Depends(get_transport_service)
):
    """
    Returns a safe snapshot of the current interview state.
    """
    if not token.candidate_id:
        raise HTTPException(status_code=403, detail="Not a valid candidate token")
        
    try:
        return await service.get_session_snapshot(session_id, token.candidate_id)
    except ValueError as e:
        if str(e) == "Session not found":
            raise HTTPException(status_code=404, detail="Session not found")
        elif str(e) == "Forbidden":
            raise HTTPException(status_code=403, detail="Forbidden")
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/sessions/{session_id}/report",
    summary="Get Interview Report",
)
async def get_report(
    session_id: str,
    token: TokenPayload = Depends(require_role(UserRole.CANDIDATE)),
    service: InterviewTransportService = Depends(get_transport_service)
):
    """
    Placeholder for Phase 10 (Report Generation).
    """
    if not token.candidate_id:
        raise HTTPException(status_code=403, detail="Not a valid candidate token")
        
    try:
        snapshot = await service.get_session_snapshot(session_id, token.candidate_id)
    except ValueError as e:
        if str(e) == "Session not found":
            raise HTTPException(status_code=404, detail="Session not found")
        raise HTTPException(status_code=403, detail="Forbidden")
        
    if not snapshot.is_completed:
        raise HTTPException(status_code=422, detail="Interview is not completed yet")
        
    from fastapi.responses import JSONResponse
    return JSONResponse(
        status_code=status.HTTP_202_ACCEPTED,
        content={"status": "report_generation_pending"}
    )


from fastapi import UploadFile, File, Form, Response
from app.ai_interview.speech_infrastructure import (
    SpeechToTextProvider,
    OpenAIWhisperAdapter,
    STTResiliencePolicy,
    STTValidator,
    STTValidationError,
    STTFatalError,
    STTTransientError,
    TextToSpeechProvider,
    TTSResiliencePolicy,
    TTSFatalError,
    TTSTransientError
)
from app.ai_interview.speech_infrastructure.stt.sarvam_saaras_adapter import SarvamSaarasAdapter
from app.ai_interview.speech_infrastructure.tts.sarvam_bulbul_adapter import SarvamBulbulAdapter
from app.config.settings import settings
import logging

logger = logging.getLogger(__name__)

def get_stt_provider() -> SpeechToTextProvider:
    if settings.SPEECH_STT_PROVIDER.lower() == "sarvam":
        return SarvamSaarasAdapter(
            api_key=settings.SARVAM_API_KEY, 
            model=settings.SARVAM_STT_MODEL,
            timeout=settings.STT_MAX_OPERATION_TIME_SECONDS
        )
    return OpenAIWhisperAdapter()

def get_tts_provider() -> TextToSpeechProvider:
    if settings.SPEECH_TTS_PROVIDER.lower() == "sarvam":
        return SarvamBulbulAdapter(
            api_key=settings.SARVAM_API_KEY,
            model=settings.SARVAM_TTS_MODEL,
            timeout=settings.TTS_MAX_OPERATION_TIME_SECONDS
        )
    # Fallback to a dummy if needed, but we assume sarvam is default for TTS
    return SarvamBulbulAdapter(api_key=settings.SARVAM_API_KEY)

# Active transcriptions tracker for MVP
active_transcriptions = set()

@router.post(
    "/sessions/{session_id}/questions/{question_record_id}/transcribe",
    summary="Transcribe candidate audio",
)
async def transcribe_audio(
    session_id: str,
    question_record_id: str,
    transcription_request_id: str = Form(...),
    file: UploadFile = File(...),
    token: TokenPayload = Depends(require_role(UserRole.CANDIDATE)),
    stt_provider: SpeechToTextProvider = Depends(get_stt_provider),
    transport: InterviewTransportService = Depends(get_transport_service)
):
    """
    Phase 11: Speech-to-Text boundary.
    Strictly purely external evidence extraction. Does NOT mutate session.
    """
    if not token.candidate_id:
        raise HTTPException(status_code=403, detail="Not a valid candidate token")
        
    # 1. Active transcription concurrency check
    if session_id in active_transcriptions:
        raise HTTPException(status_code=429, detail="Only one active transcription allowed per session.")
    
    active_transcriptions.add(session_id)
    
    try:
        # 2. Strict Correlation Validation
        try:
            snapshot = await transport.get_session_snapshot(session_id, token.candidate_id)
        except ValueError as e:
            if str(e) == "Session not found":
                raise HTTPException(status_code=404, detail="Session not found")
            raise HTTPException(status_code=403, detail="Forbidden")
            
        if snapshot.is_completed or snapshot.is_failed:
            raise HTTPException(status_code=400, detail="Interview is already in a terminal state.")
            
        if not snapshot.current_question or snapshot.current_question.record_id != question_record_id:
            raise HTTPException(status_code=400, detail="Question is not currently answerable or does not match.")
        
        # 3. Audio Size & Streaming limits
        MAX_AUDIO_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB
        
        audio_bytes = bytearray()
        while True:
            chunk = await file.read(64 * 1024)
            if not chunk:
                break
            audio_bytes.extend(chunk)
            if len(audio_bytes) > MAX_AUDIO_SIZE_BYTES:
                raise HTTPException(status_code=413, detail="Audio file exceeds 10MB limit.")
                
        if not audio_bytes:
            raise HTTPException(status_code=400, detail="Empty audio file.")
            
        # 4. MIME validation (defensive)
        allowed_mimes = ["audio/webm", "audio/mp4", "audio/mp3", "audio/wav", "audio/mpeg", "audio/ogg"]
        if file.content_type not in allowed_mimes:
            raise HTTPException(status_code=415, detail=f"Unsupported MIME type: {file.content_type}")
            
        # 5. Call Provider via Resilience Policy
        policy = STTResiliencePolicy(max_attempts=3)
        try:
            result = await policy.execute(stt_provider.transcribe, bytes(audio_bytes), file.content_type)
        except STTFatalError as e:
            raise HTTPException(status_code=400, detail=f"Transcription failed fatally: {e}")
        except STTTransientError as e:
            raise HTTPException(status_code=503, detail=f"Transcription provider unavailable: {e}")
            
        # 6. Validate Transcript
        try:
            STTValidator.validate(result)
        except STTValidationError as e:
            raise HTTPException(status_code=400, detail=str(e))
            
        return {
            "session_id": session_id,
            "question_record_id": question_record_id,
            "transcription_request_id": transcription_request_id,
            "transcript": result.transcript,
            "language": result.language,
            "duration_ms": result.duration_ms
        }
        
    finally:
        active_transcriptions.discard(session_id)


@router.post(
    "/sessions/{session_id}/questions/{question_record_id}/speech",
    summary="Synthesize authoritative question text",
)
async def synthesize_speech(
    session_id: str,
    question_record_id: str,
    token: TokenPayload = Depends(require_role(UserRole.CANDIDATE)),
    tts_provider: TextToSpeechProvider = Depends(get_tts_provider),
    transport: InterviewTransportService = Depends(get_transport_service)
):
    """
    Phase 11.5: Text-to-Speech boundary.
    Strictly purely presentation. Does NOT mutate session.
    Reads authoritative text directly from the persisted QuestionRecord.
    """
    if not token.candidate_id:
        raise HTTPException(status_code=403, detail="Not a valid candidate token")
        
    # 1. Strict Correlation Validation
    try:
        snapshot = await transport.get_session_snapshot(session_id, token.candidate_id)
    except ValueError as e:
        if str(e) == "Session not found":
            raise HTTPException(status_code=404, detail="Session not found")
        raise HTTPException(status_code=403, detail="Forbidden")
        
    if not snapshot.current_question or snapshot.current_question.record_id != question_record_id:
        raise HTTPException(status_code=400, detail="Question is not currently active or does not match.")
        
    question_text = snapshot.current_question.question_text
    
    if not question_text:
        raise HTTPException(status_code=400, detail="Question text is empty.")
        
    # 2. Call Provider via Resilience Policy
    policy = TTSResiliencePolicy(max_attempts=settings.TTS_MAX_ATTEMPTS)
    try:
        # Assuming language comes from snapshot/session if available, but for MVP let's use default hi-IN in Sarvam
        result = await policy.execute(tts_provider.synthesize, question_text, None)
    except TTSFatalError as e:
        raise HTTPException(status_code=400, detail=f"Speech synthesis failed fatally: {e}")
    except TTSTransientError as e:
        raise HTTPException(status_code=503, detail=f"Speech synthesis provider unavailable: {e}")
        
    # 3. Return Binary Audio
    return Response(content=result.audio_bytes, media_type=result.mime_type)