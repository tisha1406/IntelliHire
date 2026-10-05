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

def get_result_service():
    from app.services.interview_result_service import InterviewResultService
    return InterviewResultService()

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
    service: InterviewTransportService = Depends(get_transport_service),
    result_service = Depends(get_result_service)
):
    """
    Returns the real interview result report for an authenticated candidate.

    Ownership is enforced via get_session_snapshot() which raises ValueError
    if the session does not exist or belongs to a different candidate.

    State handling:
      A. Session not found             → 404
      B. Session belongs to other cand → 403
      C. Session not yet completed     → 200 has_report=False, status=IN_PROGRESS
      D. Completed, no evaluations     → 200 has_report=False, status=COMPLETED_NO_DATA
      E. Completed with evaluations    → 200 has_report=True  with real scores

    D-02: the exact shape returned here is now fully documented by
    app.schemas.candidate_portal.ReportResponse (reconciled against this
    service's live output, including D-01's topic_evidence/requirement_coverage).
    response_model is deliberately NOT attached to this route: this endpoint
    returns two structurally different shapes (the early-return dict above
    vs. the full E-case dict), and introducing FastAPI response validation
    here for the first time is a behavior change in its own right (a
    previously-unvalidated endpoint could start raising 500s on any future
    edge case not perfectly covered by the schema). ReportResponse remains
    available for explicit validation (see
    tests/unit/test_report_response_schema.py) without taking on that risk.
    """
    if not token.candidate_id:
        raise HTTPException(status_code=403, detail="Not a valid candidate token")

    # --- A/B: existence + ownership check via existing mechanism ---
    try:
        await service.get_session_snapshot(session_id, token.candidate_id)
    except ValueError as e:
        if str(e) == "Session not found":
            raise HTTPException(status_code=404, detail="Session not found")
        raise HTTPException(status_code=403, detail="Forbidden")

    # --- C/D/E: generate real report from InterviewResultService ---
    try:
        report = await result_service.generate_result_report(session_id)
    except ValueError as e:
        # session_id known to exist (ownership already verified); re-raise as 500
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="Failed to generate interview report."
        )

    return report


@router.get(
    "/sessions/{session_id}/report/pdf",
    summary="Download Interview Report as PDF",
)
async def get_report_pdf(
    session_id: str,
    token: TokenPayload = Depends(require_role(UserRole.CANDIDATE)),
    service: InterviewTransportService = Depends(get_transport_service),
    result_service = Depends(get_result_service)
):
    """
    D-05: real PDF rendering of the exact same report get_report() returns
    above -- same ownership check, same InterviewResultService call, no
    duplicate report-calculation logic. See app/reports/report_generator.py
    and app/reports/pdf_renderer.py.
    """
    from fastapi import Response
    from app.reports.report_generator import generate_report_pdf

    if not token.candidate_id:
        raise HTTPException(status_code=403, detail="Not a valid candidate token")

    try:
        await service.get_session_snapshot(session_id, token.candidate_id)
    except ValueError as e:
        if str(e) == "Session not found":
            raise HTTPException(status_code=404, detail="Session not found")
        raise HTTPException(status_code=403, detail="Forbidden")

    try:
        pdf_bytes = await generate_report_pdf(session_id, result_service)
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to generate interview report PDF.")

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=interview_report_{session_id}.pdf"},
    )


from fastapi import UploadFile, File, Form, Response
import struct
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


def _validate_wav_binary(audio_bytes: bytearray, log: logging.Logger) -> None:
    """
    Perform non-blocking WAV binary validation for diagnostic purposes.
    Logs [INTERVIEW] WAV_VALIDATION with structural and amplitude information.
    Never raises — only logs warnings. Does NOT log audio bytes or transcript content.
    """
    data = bytes(audio_bytes)
    size = len(data)
    try:
        # Check minimum size for a valid WAV header (44 bytes)
        if size < 44:
            log.warning(f"[INTERVIEW] WAV_VALIDATION size_bytes={size} riff=false wave=false reason=file_too_small")
            return

        # RIFF chunk
        riff = data[0:4] == b'RIFF'
        wave = data[8:12] == b'WAVE'
        fmt  = data[12:16] == b'fmt '
        dat  = data[36:40] == b'data'

        if not (riff and wave):
            log.warning(
                f"[INTERVIEW] WAV_VALIDATION "
                f"riff={riff} wave={wave} fmt={fmt} data={dat} "
                f"size_bytes={size} reason=invalid_riff_wave_header"
            )
            return

        # fmt chunk fields (little-endian)
        audio_format   = struct.unpack_from('<H', data, 20)[0]  # 1 = PCM
        num_channels   = struct.unpack_from('<H', data, 22)[0]
        sample_rate    = struct.unpack_from('<I', data, 24)[0]
        byte_rate      = struct.unpack_from('<I', data, 28)[0]
        block_align    = struct.unpack_from('<H', data, 32)[0]
        bits_per_sample = struct.unpack_from('<H', data, 34)[0]
        data_chunk_size = struct.unpack_from('<I', data, 40)[0]

        pcm_format_valid = (audio_format == 1)
        sample_rate_ok   = (sample_rate > 0)
        channels_ok      = (num_channels > 0)
        bits_ok          = bits_per_sample in (8, 16, 24, 32)
        data_ok          = (data_chunk_size > 0)

        # RMS amplitude check on PCM samples (16-bit only for simplicity)
        rms_level = 0.0
        nonzero_samples = 0
        pcm_data = data[44:44 + data_chunk_size]

        if bits_per_sample == 16 and len(pcm_data) >= 2:
            num_samples = len(pcm_data) // 2
            samples = struct.unpack_from(f'<{num_samples}h', pcm_data)
            sum_sq = sum(s * s for s in samples)
            rms_level = (sum_sq / num_samples) ** 0.5
            nonzero_samples = sum(1 for s in samples if s != 0)

        log.warning(
            f"[INTERVIEW] WAV_VALIDATION "
            f"riff={riff} wave={wave} fmt={fmt} data_chunk={dat} "
            f"pcm_format={audio_format} pcm_format_valid={pcm_format_valid} "
            f"sample_rate={sample_rate} sample_rate_ok={sample_rate_ok} "
            f"channels={num_channels} channels_ok={channels_ok} "
            f"bits={bits_per_sample} bits_ok={bits_ok} "
            f"data_bytes={data_chunk_size} data_ok={data_ok} "
            f"nonzero_samples={nonzero_samples} "
            f"rms_level={rms_level:.2f}"
        )

        if rms_level < 1.0 and bits_per_sample == 16:
            log.warning(
                f"[INTERVIEW] WAV_VALIDATION_WARNING rms_level={rms_level:.4f} "
                f"nonzero_samples={nonzero_samples} "
                f"reason=audio_may_be_silent_or_corrupt"
            )

    except Exception as e:
        log.warning(f"[INTERVIEW] WAV_VALIDATION_EXCEPTION reason={e}")



def get_stt_provider() -> SpeechToTextProvider:
    if settings.SPEECH_STT_PROVIDER.lower() == "sarvam":
        return SarvamSaarasAdapter(
            api_key=settings.SARVAM_API_KEY, 
            model=settings.SARVAM_STT_MODEL,
            language_code=settings.SARVAM_STT_LANGUAGE,
            timeout=settings.STT_MAX_OPERATION_TIME_SECONDS
        )
    return OpenAIWhisperAdapter()

def get_tts_provider() -> TextToSpeechProvider:
    if settings.SPEECH_TTS_PROVIDER.lower() == "sarvam":
        return SarvamBulbulAdapter(
            api_key=settings.SARVAM_API_KEY,
            model=settings.SARVAM_TTS_MODEL,
            language_code=settings.SARVAM_TTS_LANGUAGE,
            speaker=settings.SARVAM_TTS_SPEAKER,
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
        allowed_mimes = ["audio/webm", "audio/mp4", "audio/mp3", "audio/wav", "audio/x-wav", "audio/wave", "audio/mpeg", "audio/ogg"]
        if file.content_type not in allowed_mimes:
            raise HTTPException(status_code=415, detail=f"Unsupported MIME type: {file.content_type}")
            
        logger.warning(
            f"[INTERVIEW] STT_REQUEST "
            f"session={session_id} "
            f"question={question_record_id} "
            f"filename={file.filename} "
            f"content_type={file.content_type} "
            f"size_bytes={len(audio_bytes)} "
            f"provider=sarvam "
            f"model={settings.SARVAM_STT_MODEL} "
            f"language={settings.SARVAM_STT_LANGUAGE}"
        )

        # 4b. WAV binary validation (only if content type indicates WAV)
        if "wav" in (file.content_type or ""):
            _validate_wav_binary(audio_bytes, logger)
            
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
        
    # 2. Extract Voice Configuration
    ALLOWED_VOICES = {"shubh", "simran", "rohan", "ishita", "sunny"}
    effective_voice = "shubh" # Ultimate fallback
    campaign_language = None
    
    try:
        db = get_database()
        session_repo = InterviewSessionRepository(db.interview_sessions)
        session = await session_repo.get_by_id(session_id)
        
        # 1. Try session snapshot first
        if session and getattr(session, "voice_id", None):
            effective_voice = session.voice_id
            
        # 2. Fallback to Campaign for legacy sessions or language
        if session and session.campaign_id:
            campaign_repo = CampaignRepository()
            campaign = await campaign_repo.get_by_id(session.campaign_id)
            if campaign:
                if not getattr(session, "voice_id", None) and getattr(campaign, "voice_id", None):
                    effective_voice = campaign.voice_id
                if getattr(campaign, "language", None):
                    campaign_language = campaign.language
                    
        # 3. Validate against allowlist
        if effective_voice.lower() not in ALLOWED_VOICES:
            effective_voice = "shubh"
            
    except Exception as e:
        logger.warning(f"Could not retrieve voice for session {session_id}: {e}")

    # 3. Call Provider via Resilience Policy
    policy = TTSResiliencePolicy(max_attempts=settings.TTS_MAX_ATTEMPTS)
    try:
        result = await policy.execute(tts_provider.synthesize, question_text, campaign_language, effective_voice)
    except TTSFatalError as e:
        raise HTTPException(status_code=400, detail=f"Speech synthesis failed fatally: {e}")
    except TTSTransientError as e:
        raise HTTPException(status_code=503, detail=f"Speech synthesis provider unavailable: {e}")
        
    # 3. Return Binary Audio
    return Response(content=result.audio_bytes, media_type=result.mime_type)