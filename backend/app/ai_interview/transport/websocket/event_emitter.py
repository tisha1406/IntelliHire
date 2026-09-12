"""
Phase 9 — WebSocket Event EventEmitter
======================================
Builds typed ServerEvent instances and sends them via the ConnectionManager.
Maintains a per-connection monotonic `sequence` counter.
"""
from typing import Optional
from app.ai_interview.transport.websocket.connection_manager import connection_manager
from app.ai_interview.transport.schemas.ws_events import (
    ServerEvent,
    ConnectionReadyEvent, ConnectionReadyData,
    SessionSnapshotEvent, SessionSnapshotData,
    InterviewStartedEvent, InterviewStartedData,
    QuestionGeneratingEvent, QuestionGeneratingData,
    QuestionReadyEvent, QuestionReadyData,
    AnswerReceivedEvent, AnswerReceivedData,
    EvaluationProcessingEvent, EvaluationProcessingData,
    EvaluationCompleteEvent, EvaluationCompleteData,
    DecisionReadyEvent, DecisionReadyData,
    NextQuestionReadyEvent,
    InterviewPausedEvent, InterviewResumedEvent,
    InterviewCompletedEvent, InterviewCompletedData,
    InterviewFailedEvent, InterviewFailedData,
    ErrorEvent, PongEvent
)
from app.ai_interview.transport.schemas.ws_errors import WsErrorPayload

class InterviewEventEmitter:
    def __init__(self):
        # Maps session_id -> monotonic sequence number
        self._sequences: dict[str, int] = {}

    def _next_sequence(self, session_id: str) -> int:
        seq = self._sequences.get(session_id, -1) + 1
        self._sequences[session_id] = seq
        return seq

    def reset_sequence(self, session_id: str) -> None:
        """Called on reconnect to reset sequence to 0."""
        self._sequences[session_id] = 0

    async def _send(self, session_id: str, event: ServerEvent) -> bool:
        event.sequence = self._next_sequence(session_id)
        return await connection_manager.send_event(session_id, event.model_dump_json())

    # -----------------------------------------------------------------------
    # Typed Emitters
    # -----------------------------------------------------------------------
    async def emit_connection_ready(self, session_id: str, data: ConnectionReadyData) -> bool:
        return await self._send(session_id, ConnectionReadyEvent(session_id=session_id, data=data))

    async def emit_session_snapshot(self, session_id: str, data: SessionSnapshotData) -> bool:
        return await self._send(session_id, SessionSnapshotEvent(session_id=session_id, data=data))

    async def emit_interview_started(self, session_id: str, data: InterviewStartedData, correlation_id: Optional[str] = None) -> bool:
        return await self._send(session_id, InterviewStartedEvent(session_id=session_id, data=data, correlation_id=correlation_id))

    async def emit_question_generating(self, session_id: str, data: QuestionGeneratingData, correlation_id: Optional[str] = None) -> bool:
        return await self._send(session_id, QuestionGeneratingEvent(session_id=session_id, data=data, correlation_id=correlation_id))

    async def emit_question_ready(self, session_id: str, data: QuestionReadyData, correlation_id: Optional[str] = None) -> bool:
        return await self._send(session_id, QuestionReadyEvent(session_id=session_id, data=data, correlation_id=correlation_id))

    async def emit_answer_received(self, session_id: str, data: AnswerReceivedData, correlation_id: Optional[str] = None) -> bool:
        return await self._send(session_id, AnswerReceivedEvent(session_id=session_id, data=data, correlation_id=correlation_id))

    async def emit_evaluation_processing(self, session_id: str, data: EvaluationProcessingData, correlation_id: Optional[str] = None) -> bool:
        return await self._send(session_id, EvaluationProcessingEvent(session_id=session_id, data=data, correlation_id=correlation_id))

    async def emit_evaluation_complete(self, session_id: str, data: EvaluationCompleteData, correlation_id: Optional[str] = None) -> bool:
        return await self._send(session_id, EvaluationCompleteEvent(session_id=session_id, data=data, correlation_id=correlation_id))

    async def emit_decision_ready(self, session_id: str, data: DecisionReadyData, correlation_id: Optional[str] = None) -> bool:
        return await self._send(session_id, DecisionReadyEvent(session_id=session_id, data=data, correlation_id=correlation_id))

    async def emit_next_question_ready(self, session_id: str, data: QuestionReadyData, correlation_id: Optional[str] = None) -> bool:
        return await self._send(session_id, NextQuestionReadyEvent(session_id=session_id, data=data, correlation_id=correlation_id))

    async def emit_interview_paused(self, session_id: str, correlation_id: Optional[str] = None) -> bool:
        return await self._send(session_id, InterviewPausedEvent(session_id=session_id, correlation_id=correlation_id))

    async def emit_interview_resumed(self, session_id: str, correlation_id: Optional[str] = None) -> bool:
        return await self._send(session_id, InterviewResumedEvent(session_id=session_id, correlation_id=correlation_id))

    async def emit_interview_completed(self, session_id: str, data: InterviewCompletedData, correlation_id: Optional[str] = None) -> bool:
        return await self._send(session_id, InterviewCompletedEvent(session_id=session_id, data=data, correlation_id=correlation_id))

    async def emit_interview_failed(self, session_id: str, data: InterviewFailedData, correlation_id: Optional[str] = None) -> bool:
        return await self._send(session_id, InterviewFailedEvent(session_id=session_id, data=data, correlation_id=correlation_id))

    async def emit_error(self, session_id: str, payload: WsErrorPayload) -> bool:
        # payload already includes command_id mapping to correlation_id
        return await self._send(session_id, ErrorEvent(session_id=session_id, data=payload, correlation_id=payload.command_id))

    async def emit_pong(self, session_id: str, correlation_id: Optional[str] = None) -> bool:
        return await self._send(session_id, PongEvent(session_id=session_id, correlation_id=correlation_id))

event_emitter = InterviewEventEmitter()
