from app.ai_interview.schemas.session import InterviewSessionSchema
from app.ai_interview.core.enums import InterviewState
from app.ai_interview.runtime.schemas import RuntimeDecision
from app.ai_interview.runtime.enums import RuntimeAction
from app.ai_interview.runtime.state_machine import StateMachine
from app.ai_interview.runtime.validators import Validators
from app.ai_interview.runtime.topic_progression_engine import TopicProgressionEngine
from app.ai_interview.runtime.completion_engine import CompletionEngine

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
                return RuntimeDecision(
                    current_state=session.state,
                    allowed_action=RuntimeAction.COMPLETE,
                    active_topic_id=None,
                    should_complete=True,
                    completion_trace=trace,
                    reason_codes=trace.reason_codes
                )
                
            # If not complete, determine topic
            next_topic = TopicProgressionEngine.get_next_active_topic(session)
            if next_topic is None:
                # No topics remain but completion not allowed? (e.g. Budget check prevented it earlier, but here no topics are unresolved).
                # Wait, CompletionEngine forces should_complete=True if all mandatory are attempted (even if abandoned).
                # But if we reach here with no topics, complete.
                return RuntimeDecision(
                    current_state=session.state,
                    allowed_action=RuntimeAction.COMPLETE,
                    active_topic_id=None,
                    should_complete=True,
                    completion_trace=trace,
                    reason_codes=trace.reason_codes
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
            
        elif action == RuntimeAction.FAIL:
            StateMachine.assert_transition(session.state, InterviewState.FAILED)
            session.state = InterviewState.FAILED
            
        elif action == RuntimeAction.ADVANCE_TOPIC:
            next_topic = TopicProgressionEngine.get_next_active_topic(session)
            if next_topic:
                session.current_topic_id = next_topic.topic_id
