"""
Phase 9 — Interview Transport Service
=====================================
Executes typed commands from the WebSocket command router.
Interfaces with Phase 8 persistence and Phase 7 coordinator.
Enforces all persist-before-emit rules and concurrency invariants.
"""
import asyncio
import logging
from typing import Optional

from app.config.settings import settings
from app.ai_interview.core.enums import InterviewState
from app.ai_interview.runtime.enums import RuntimeAction
from app.ai_interview.runtime.runtime_controller import RuntimeController
from app.ai_interview.orchestration.interview_turn_coordinator import InterviewTurnCoordinator
from app.ai_interview.answer_engine.schemas import AnswerSubmission

from app.ai_interview.persistence.repository import InterviewSessionRepository
from app.ai_interview.persistence.exceptions import (
    ClaimAlreadyHeldError, OptimisticConcurrencyError, FencingTokenError,
    IdempotencyConflictError, PersistenceInvariantError, SessionNotFoundError
)
from app.ai_interview.transport import get_interview_executor
from app.ai_interview.transport.websocket.authenticator import WsConnectionContext
from app.ai_interview.transport.websocket.event_emitter import event_emitter
from app.ai_interview.transport.schemas.ws_commands import (
    StartInterviewCommand, SubmitAnswerCommand, PauseInterviewCommand, ResumeInterviewCommand
)
from app.ai_interview.transport.schemas.ws_events import (
    ConnectionReadyData, SessionSnapshotData, QuestionSnapshotData, InterviewStartedData,
    QuestionGeneratingData, QuestionReadyData, AnswerReceivedData,
    EvaluationProcessingData, EvaluationCompleteData, DecisionReadyData,
    InterviewCompletedData
)
from app.ai_interview.transport.schemas.ws_errors import (
    WsErrorCode, build_error_payload
)

from app.repositories.resume_repository import ResumeRepository
from app.repositories.interview_mode_repository import InterviewModeRepository
from app.ai_interview.schemas.interview_mode import InterviewModeDefinition
from app.ai_interview.transport.services.resume_context_bridge import ResumeContextBridge
from app.ai_interview.resume_processing.schemas import CandidateInterviewContext
from app.ai_interview.schemas.session import InterviewSessionSchema

logger = logging.getLogger("intellihire")


class InterviewTransportService:
    def __init__(
        self,
        session_repo: InterviewSessionRepository,
        resume_repo: ResumeRepository,
        mode_repo: InterviewModeRepository,
        coordinator: InterviewTurnCoordinator
    ):
        self.repo = session_repo
        self.resume_repo = resume_repo
        self.mode_repo = mode_repo
        self.coordinator = coordinator

    async def _load_candidate_context(self, candidate_id: str) -> CandidateInterviewContext:
        resume_doc = await self.resume_repo.get_by_candidate(candidate_id)
        if not resume_doc:
            raise RuntimeError("Resume analysis not found")
        return ResumeContextBridge.build(resume_doc, candidate_id)

    async def _load_mode(self, mode_id: str, version: int) -> InterviewModeDefinition:
        mode_doc = await self.mode_repo.get_by_mode_id(mode_id)
        if not mode_doc:
            raise RuntimeError(f"Mode {mode_id} not found")
        return InterviewModeDefinition.model_validate(mode_doc)

    async def _handle_persistence_error(self, session_id: str, command_id: str, e: Exception) -> None:
        code = WsErrorCode.PERSISTENCE_FAILED
        payload = build_error_payload(code, command_id=command_id)
        await event_emitter.emit_error(session_id, payload)
        logger.warning({
            "event": "ws_persistence_error",
            "session_id": session_id,
            "error_type": type(e).__name__,
            "error_code": code.value
        })

    def _build_question_snapshot(self, question) -> QuestionSnapshotData:
        return QuestionSnapshotData(
            record_id=question.record_id,
            question_text=question.question_text,
            topic_id=question.topic_id,
            topic_name=None,  # We could map from blueprint if needed
            turn_number=question.turn_number,
            question_type=question.question_type.value,
            difficulty=question.difficulty.value,
            status=question.status.value
        )

    def _build_session_snapshot(self, session: InterviewSessionSchema, **recovery_hints) -> SessionSnapshotData:
        last_q = session.question_history[-1] if session.question_history else None
        
        return SessionSnapshotData(
            session_id=session.session_id,
            interview_state=session.state.value,
            questions_asked_total=session.questions_asked_total,
            total_question_budget=session.blueprint.total_question_budget,
            min_questions=session.blueprint.min_questions,
            current_topic_id=session.current_topic_id,
            current_question=self._build_question_snapshot(last_q) if last_q and last_q.status.value == "dispatched" else None,
            is_paused=session.state == InterviewState.PAUSED,
            is_completed=session.state == InterviewState.COMPLETED,
            is_failed=session.state == InterviewState.FAILED,
            waiting_for_answer=bool(last_q and last_q.status.value == "dispatched"),
            **recovery_hints
        )

    # =========================================================================
    # RECOVERY / SNAPSHOT (GET / REST & WS Reconnect)
    # =========================================================================

    async def get_session_snapshot(self, session_id: str, candidate_id: str) -> SessionSnapshotData:
        try:
            session = await self.repo.get_by_id(session_id)
        except SessionNotFoundError:
            raise ValueError("Session not found")
        if session.candidate_id != candidate_id:
            raise ValueError("Forbidden")
        return self._build_session_snapshot(session)

    async def handle_reconnect(self, session_id: str, context: WsConnectionContext) -> None:
        """
        Called immediately after a socket is authenticated and registered.
        Responsible for sending the current state and replaying pending questions.
        """
        event_emitter.reset_sequence(session_id)
        
        # Always fetch fresh authoritative state on reconnect
        session = await self.repo.get_by_id(session_id)
        
        # 1. Connection Ready
        await event_emitter.emit_connection_ready(
            session_id,
            ConnectionReadyData(candidate_id=session.candidate_id, session_state=session.state.value)
        )
        
        # 2. Analyze state for recovery hints
        last_q = session.question_history[-1] if session.question_history else None
        recovery_hints = {}
        
        if last_q:
            from datetime import datetime, timezone
            now = datetime.now(timezone.utc)
            if last_q.status.value == "evaluating":
                if last_q.evaluation_claim and last_q.evaluation_claim.expires_at > now:
                    recovery_hints["evaluation_in_progress"] = True
                else:
                    recovery_hints["pending_evaluation"] = True  # Claim expired, needs re-eval
            elif last_q.status.value in ("answer_received", "evaluation_pending"):
                recovery_hints["pending_evaluation"] = True
        
        # 3. Emit Snapshot
        snapshot = self._build_session_snapshot(session, **recovery_hints)
        await event_emitter.emit_session_snapshot(session_id, snapshot)
        
        # 4. Replays & Reminders
        if session.state == InterviewState.IN_PROGRESS and last_q and last_q.status.value == "dispatched":
            await event_emitter.emit_question_ready(
                session_id, 
                QuestionReadyData(**self._build_question_snapshot(last_q).model_dump())
            )
        elif session.state == InterviewState.PAUSED:
            await event_emitter.emit_interview_paused(session_id)

    # =========================================================================
    # START INTERVIEW
    # =========================================================================

    async def handle_start_interview(self, session_id: str, command: StartInterviewCommand, context: WsConnectionContext) -> None:
        session = await self.repo.get_by_id(session_id)
        
        if session.state in (InterviewState.COMPLETED, InterviewState.FAILED):
            payload = build_error_payload(WsErrorCode.SESSION_TERMINAL, command.command_id)
            await event_emitter.emit_error(session_id, payload)
            return

        if session.state not in (InterviewState.CREATED, InterviewState.INITIALIZING):
            payload = build_error_payload(WsErrorCode.INVALID_SESSION_STATE, command.command_id)
            await event_emitter.emit_error(session_id, payload)
            return

        # 1. Acquire generation claim
        try:
            claim = await self.repo.claim_question_generation(
                session_id, 
                expected_version=session.version,
                lease_seconds=settings.GENERATION_LEASE_SECONDS
            )
        except (ClaimAlreadyHeldError, OptimisticConcurrencyError) as e:
            await self._handle_persistence_error(session_id, command.command_id, e)
            return

        # [PERSIST-BEFORE-EMIT: Claim is now in DB]
        session = await self.repo.get_by_id(session_id)
        await event_emitter.emit_question_generating(
            session_id, 
            QuestionGeneratingData(topic_id=session.current_topic_id or session.blueprint.topics[0].topic_id, turn_number=1),
            correlation_id=command.command_id
        )

        # 2. Run Engine (Synchronous thread)
        candidate_context = await self._load_candidate_context(session.candidate_id)
        mode = await self._load_mode(session.mode_id, session.mode_version)
        loop = asyncio.get_event_loop()
        
        try:
            result = await loop.run_in_executor(
                get_interview_executor(),
                self.coordinator.advance_interview,
                session, candidate_context, mode, None
            )
        except Exception as e:
            logger.exception("Engine failed during start")
            await self.repo.release_question_generation(session_id, session.version, claim.claim_id)
            await event_emitter.emit_error(session_id, build_error_payload(WsErrorCode.GENERATION_FAILED, command.command_id))
            return

        # 3. Persist Output
        if result.interview_completed:
            try:
                await self.repo.save(
                    session, 
                    expected_version=session.version,
                    generation_fencing_id=claim.claim_id
                )
            except Exception as e:
                await self._handle_persistence_error(session_id, command.command_id, e)
                return
                
            await event_emitter.emit_interview_completed(
                session_id,
                InterviewCompletedData(questions_asked_total=session.questions_asked_total, completed_at=session.completed_at.isoformat()),
                correlation_id=command.command_id
            )
            return

        if not result.question:
            await self.repo.release_question_generation(session_id, session.version, claim.claim_id)
            await event_emitter.emit_error(session_id, build_error_payload(WsErrorCode.GENERATION_FAILED, command.command_id))
            return

        # Save active question
        try:
            await self.repo.save(
                session, 
                expected_version=session.version,
                generation_fencing_id=claim.claim_id,
                idempotency_question_id=result.question.record_id
            )
        except Exception as e:
            await self._handle_persistence_error(session_id, command.command_id, e)
            return

        # [PERSIST-BEFORE-EMIT: Question is now in DB]
        await event_emitter.emit_interview_started(
            session_id,
            InterviewStartedData(
                mode_id=session.mode_id, 
                mode_version=session.mode_version,
                topics_count=len(session.blueprint.topics),
                total_question_budget=session.blueprint.total_question_budget,
                min_questions=session.blueprint.min_questions
            ),
            correlation_id=command.command_id
        )
        
        await event_emitter.emit_question_ready(
            session_id,
            QuestionReadyData(**self._build_question_snapshot(result.question).model_dump()),
            correlation_id=command.command_id
        )

    # =========================================================================
    # SUBMIT ANSWER
    # =========================================================================

    async def handle_submit_answer(self, session_id: str, command: SubmitAnswerCommand, context: WsConnectionContext) -> None:
        session = await self.repo.get_by_id(session_id)
        
        if session.state in (InterviewState.COMPLETED, InterviewState.FAILED):
            await event_emitter.emit_error(session_id, build_error_payload(WsErrorCode.SESSION_TERMINAL, command.command_id))
            return

        # Validate Question
        target_q_id = command.payload.question_record_id
        active_question = next((q for q in session.question_history if q.record_id == target_q_id), None)
        
        if not active_question:
            await event_emitter.emit_error(session_id, build_error_payload(WsErrorCode.QUESTION_NOT_FOUND, command.command_id))
            return

        if active_question.status.value == "evaluated":
            await event_emitter.emit_error(session_id, build_error_payload(WsErrorCode.QUESTION_STATUS_CONFLICT, command.command_id))
            return

        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        if active_question.status.value == "evaluating" and active_question.evaluation_claim and active_question.evaluation_claim.expires_at > now:
            await event_emitter.emit_error(session_id, build_error_payload(WsErrorCode.EVALUATION_IN_PROGRESS, command.command_id))
            return

        # 1. Acquire BOTH Evaluation and Generation claims (Phase 9 invariant for single-save)
        try:
            eval_claim = await self.repo.claim_evaluation(
                session_id, 
                question_record_id=target_q_id,
                expected_version=session.version,
                lease_seconds=settings.EVALUATION_LEASE_SECONDS
            )
            # version was incremented by claim_evaluation, so +1
            gen_claim = await self.repo.claim_question_generation(
                session_id,
                expected_version=session.version + 1,
                lease_seconds=settings.GENERATION_LEASE_SECONDS
            )
        except (ClaimAlreadyHeldError, OptimisticConcurrencyError) as e:
            await self._handle_persistence_error(session_id, command.command_id, e)
            return

        # Reload session at N+2
        session = await self.repo.get_by_id(session_id)
        
        await event_emitter.emit_answer_received(
            session_id,
            AnswerReceivedData(question_record_id=target_q_id, answer_length=len(command.payload.answer_text)),
            correlation_id=command.command_id
        )
        await event_emitter.emit_evaluation_processing(
            session_id,
            EvaluationProcessingData(question_record_id=target_q_id),
            correlation_id=command.command_id
        )

        # 2. Run Engine
        submission = AnswerSubmission(
            session_id=session_id,
            question_record_id=target_q_id,
            answer_text=command.payload.answer_text
        )
        candidate_context = await self._load_candidate_context(session.candidate_id)
        mode = await self._load_mode(session.mode_id, session.mode_version)
        loop = asyncio.get_event_loop()
        
        try:
            result = await loop.run_in_executor(
                get_interview_executor(),
                self.coordinator.advance_interview,
                session, candidate_context, mode, submission
            )
        except Exception as e:
            logger.exception("Engine failed during evaluation/generation")
            # Release both claims on failure
            await self.repo.release_evaluation(session_id, target_q_id, session.version, eval_claim.claim_id)
            await self.repo.release_question_generation(session_id, session.version + 1, gen_claim.claim_id)
            await event_emitter.emit_error(session_id, build_error_payload(WsErrorCode.EVALUATION_FAILED, command.command_id))
            return

        # 3. Persist Output
        if result.interview_completed:
            try:
                # Discard gen_claim since no question was generated, just let it expire or clear implicitly
                await self.repo.save(
                    session,
                    expected_version=session.version,
                    evaluation_fencing_id=eval_claim.claim_id,
                    idempotency_evaluation_question_id=target_q_id
                )
            except Exception as e:
                await self._handle_persistence_error(session_id, command.command_id, e)
                return
                
            if result.evaluation:
                await event_emitter.emit_evaluation_complete(
                    session_id,
                    EvaluationCompleteData(
                        question_record_id=target_q_id,
                        topic_id=result.evaluation.get("topic_id", ""),
                        overall_score=result.evaluation.get("overall_score", 0.0),
                        follow_up_signal=result.evaluation.get("follow_up_signal", "NONE"),
                        qualitative_coverage_signal=result.evaluation.get("qualitative_coverage_signal", "NOT_COVERED")
                    ),
                    correlation_id=command.command_id
                )
                
            # Phase 12: Generate final result and propagate to Candidate
            try:
                from app.services.interview_result_service import InterviewResultService
                from app.repositories.candidate_repository import CandidateRepository
                
                result_service = InterviewResultService()
                report = await result_service.generate_result_report(session_id)
                
                if report and report.get("has_report"):
                    cand_repo = CandidateRepository()
                    overall_score = report.get("overall_score", 0)
                    ai_recommendations = report.get("company_remarks", "")
                    
                    # Update candidate with final scores and state
                    await cand_repo.update(
                        str(session.candidate_id),
                        {
                            "interviewScore": overall_score,
                            "aiMatch": overall_score,
                            "aiRecommendations": ai_recommendations,
                            "currentStage": "AI Interview Completed",
                            "status": "Interviewed",
                        }
                    )
            except Exception as e:
                logger.error(f"Failed to propagate result to candidate {session.candidate_id}: {e}")

            await event_emitter.emit_decision_ready(session_id, DecisionReadyData(action="complete"), correlation_id=command.command_id)
            await event_emitter.emit_interview_completed(
                session_id,
                InterviewCompletedData(questions_asked_total=session.questions_asked_total, completed_at=session.completed_at.isoformat()),
                correlation_id=command.command_id
            )
            return

        # Interview continues
        try:
            await self.repo.save(
                session,
                expected_version=session.version,
                evaluation_fencing_id=eval_claim.claim_id,
                generation_fencing_id=gen_claim.claim_id,
                idempotency_evaluation_question_id=target_q_id,
                idempotency_question_id=result.question.record_id if result.question else None
            )
        except Exception as e:
            await self._handle_persistence_error(session_id, command.command_id, e)
            return

        # Emit Evaluation
        if result.evaluation:
            await event_emitter.emit_evaluation_complete(
                session_id,
                EvaluationCompleteData(
                    question_record_id=target_q_id,
                    topic_id=result.evaluation.get("topic_id", ""),
                    overall_score=result.evaluation.get("overall_score", 0.0),
                    follow_up_signal=result.evaluation.get("follow_up_signal", "NONE"),
                    qualitative_coverage_signal=result.evaluation.get("qualitative_coverage_signal", "NOT_COVERED")
                ),
                correlation_id=command.command_id
            )
            
        await event_emitter.emit_decision_ready(session_id, DecisionReadyData(action="next_question", topic_id=result.current_topic_id), correlation_id=command.command_id)
        
        # Emit next question
        if result.question:
            await event_emitter.emit_next_question_ready(
                session_id,
                QuestionReadyData(**self._build_question_snapshot(result.question).model_dump()),
                correlation_id=command.command_id
            )

    # =========================================================================
    # PAUSE & RESUME
    # =========================================================================

    async def handle_pause(self, session_id: str, command: PauseInterviewCommand, context: WsConnectionContext) -> None:
        session = await self.repo.get_by_id(session_id)
        if session.state != InterviewState.IN_PROGRESS:
            await event_emitter.emit_error(session_id, build_error_payload(WsErrorCode.INVALID_SESSION_STATE, command.command_id))
            return
            
        RuntimeController.execute_transition(session, RuntimeAction.PAUSE)
        
        try:
            await self.repo.save(session, expected_version=session.version)
        except Exception as e:
            await self._handle_persistence_error(session_id, command.command_id, e)
            return
            
        await event_emitter.emit_interview_paused(session_id, correlation_id=command.command_id)

    async def handle_resume(self, session_id: str, command: ResumeInterviewCommand, context: WsConnectionContext) -> None:
        session = await self.repo.get_by_id(session_id)
        if session.state != InterviewState.PAUSED:
            await event_emitter.emit_error(session_id, build_error_payload(WsErrorCode.INVALID_SESSION_STATE, command.command_id))
            return
            
        RuntimeController.execute_transition(session, RuntimeAction.RESUME)
        
        try:
            await self.repo.save(session, expected_version=session.version)
        except Exception as e:
            await self._handle_persistence_error(session_id, command.command_id, e)
            return
            
        await event_emitter.emit_interview_resumed(session_id, correlation_id=command.command_id)
        
        # Replay question if pending
        last_q = session.question_history[-1] if session.question_history else None
        if last_q and last_q.status.value == "dispatched":
            await event_emitter.emit_question_ready(
                session_id, 
                QuestionReadyData(**self._build_question_snapshot(last_q).model_dump()),
                correlation_id=command.command_id
            )
        else:
            # Just send snapshot
            snapshot = self._build_session_snapshot(session)
            await event_emitter.emit_session_snapshot(session_id, snapshot)
