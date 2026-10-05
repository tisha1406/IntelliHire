from app.ai_interview.schemas.session import InterviewSessionSchema
from app.ai_interview.core.enums import InterviewState, CompletionReason
from app.ai_interview.runtime.schemas import RuntimeDecision
from app.ai_interview.runtime.enums import RuntimeAction
from app.ai_interview.runtime.state_machine import StateMachine
from app.ai_interview.runtime.validators import Validators
from app.ai_interview.runtime.topic_progression_engine import TopicProgressionEngine
from app.ai_interview.runtime.completion_engine import CompletionEngine
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)
class RuntimeController:
    """
    Primary deterministic facade coordinating Phase 4 rules.
    It returns a RuntimeDecision and does NOT mutate arbitrary state without controlled methods.
    """

    @staticmethod
    def get_allowed_action(session: InterviewSessionSchema) -> RuntimeDecision:
        Validators.validate_session(session)
        
        # Terminal states
        if session.state in [InterviewState.COMPLETED, InterviewState.FAILED]:
            return RuntimeDecision(
                current_state=session.state,
                allowed_action=RuntimeAction.NO_ACTION,
                active_topic_id=None
            )
            
        # Initialization
        if session.state == InterviewState.CREATED:
            return RuntimeDecision(
                current_state=session.state,
                allowed_action=RuntimeAction.INITIALIZE,
                active_topic_id=None
            )
            
        # Startup
        if session.state == InterviewState.INITIALIZING:
            return RuntimeDecision(
                current_state=session.state,
                allowed_action=RuntimeAction.START,
                active_topic_id=None
            )
            
        # Paused
        if session.state == InterviewState.PAUSED:
            return RuntimeDecision(
                current_state=session.state,
                allowed_action=RuntimeAction.RESUME,
                active_topic_id=None
            )
            
        # In Progress logic
        if session.state == InterviewState.IN_PROGRESS:
            should_complete, trace = CompletionEngine.evaluate(session)
            
            if should_complete:
                # Determine and attach the typed completion reason before returning
                # so execute_transition / persistence can persist it.
                completion_reason: CompletionReason = CompletionEngine.get_completion_reason(session)
                return RuntimeDecision(
                    current_state=session.state,
                    allowed_action=RuntimeAction.COMPLETE,
                    active_topic_id=None,
                    should_complete=True,
                    completion_trace=trace,
                    reason_codes=trace.reason_codes,
                    completion_reason=completion_reason,
                )
                
            # If not complete, determine topic
            is_practice = getattr(session, "mode_id", None) == "practice"
            
            if is_practice:
                # Rigid sequential selection for practice
                next_topic = None
                from app.ai_interview.core.enums import TopicState
                for progress in session.topic_progress:
                    if progress.state not in [TopicState.COVERED, TopicState.FAILED_ABANDONED]:
                        next_topic = progress
                        break
            else:
                next_topic = TopicProgressionEngine.get_next_active_topic(session)
            
            if is_practice:
                logger.info(f"[INTERVIEW] SHADOW_PRIORITY_SKIPPED session={session.session_id} reason=practice_mode")
            elif next_topic is not None:
                priority = getattr(next_topic, "_selected_priority", "N/A")
                logger.info(
                    f"[INTERVIEW] TOPIC_SELECTED "
                    f"session={session.session_id} "
                    f"mode={session.mode_id} "
                    f"topic={next_topic.topic_id} "
                    f"priority={priority} "
                    f"reason=deterministic_priority"
                )

            if next_topic is None:
                # No topics remain — exhaust deterministically
                no_topic_reason = CompletionEngine.get_completion_reason(session)
                return RuntimeDecision(
                    current_state=session.state,
                    allowed_action=RuntimeAction.COMPLETE,
                    active_topic_id=None,
                    should_complete=True,
                    completion_trace=trace,
                    reason_codes=trace.reason_codes,
                    completion_reason=no_topic_reason,
                )
                
            if session.current_topic_id == next_topic.topic_id:
                return RuntimeDecision(
                    current_state=session.state,
                    allowed_action=RuntimeAction.NO_ACTION,
                    active_topic_id=next_topic.topic_id,
                    should_complete=False,
                    completion_trace=trace,
                    reason_codes=trace.reason_codes
                )
            else:
                return RuntimeDecision(
                    current_state=session.state,
                    allowed_action=RuntimeAction.ADVANCE_TOPIC,
                    active_topic_id=next_topic.topic_id,
                    should_complete=False,
                    completion_trace=trace,
                    reason_codes=trace.reason_codes
                )

        return RuntimeDecision(
            current_state=session.state,
            allowed_action=RuntimeAction.NO_ACTION,
            active_topic_id=None
        )

    @staticmethod
    def execute_transition(session: InterviewSessionSchema, action: RuntimeAction) -> None:
        """
        Controlled mutation boundary.
        ADVANCE_TOPIC is pure deterministic traversal, DOES NOT infer qualitative coverage.
        """
        Validators.validate_session(session)
        
        if action == RuntimeAction.NO_ACTION:
            pass
        elif action == RuntimeAction.INITIALIZE:
            StateMachine.assert_transition(session.state, InterviewState.INITIALIZING)
            session.state = InterviewState.INITIALIZING
            
        elif action == RuntimeAction.START:
            StateMachine.assert_transition(session.state, InterviewState.IN_PROGRESS)
            session.state = InterviewState.IN_PROGRESS
            
        elif action == RuntimeAction.PAUSE:
            StateMachine.assert_transition(session.state, InterviewState.PAUSED)
            session.state = InterviewState.PAUSED
            
        elif action == RuntimeAction.RESUME:
            StateMachine.assert_transition(session.state, InterviewState.IN_PROGRESS)
            session.state = InterviewState.IN_PROGRESS
            
        elif action == RuntimeAction.COMPLETE:
            StateMachine.assert_transition(session.state, InterviewState.COMPLETED)
            session.state = InterviewState.COMPLETED
            session.completed_at = datetime.now(timezone.utc)

            # D-01 supporting change: stamp TopicProgress.terminal_reason on
            # topics that were never attempted, so the result-report layer can
            # expose an honest skip_reason. This only RECORDS the completion
            # decision already made above (session.completion_reason, set by
            # the caller before this transition) onto topics it affected — it
            # does not change which topics were selected, when the interview
            # completed, or any scoring/priority logic.
            from app.ai_interview.core.enums import TopicTerminalReason
            _budget_exhaustion_reasons = {
                CompletionReason.MAX_QUESTIONS_REACHED,
                CompletionReason.BUDGET_EXHAUSTED,
            }
            for progress in session.topic_progress:
                if progress.questions_asked == 0 and progress.terminal_reason is None:
                    if session.completion_reason in _budget_exhaustion_reasons:
                        progress.terminal_reason = TopicTerminalReason.BUDGET_EXHAUSTED
                    else:
                        progress.terminal_reason = TopicTerminalReason.DEPRIORITIZED
            
        elif action == RuntimeAction.FAIL:
            StateMachine.assert_transition(session.state, InterviewState.FAILED)
            session.state = InterviewState.FAILED
            
        elif action == RuntimeAction.ADVANCE_TOPIC:
            is_practice = getattr(session, "mode_id", None) == "practice"
            if is_practice:
                next_topic = None
                from app.ai_interview.core.enums import TopicState
                for progress in session.topic_progress:
                    if progress.state not in [TopicState.COVERED, TopicState.FAILED_ABANDONED]:
                        next_topic = progress
                        break
            else:
                next_topic = TopicProgressionEngine.get_next_active_topic(session)
                
            if next_topic:
                session.current_topic_id = next_topic.topic_id
