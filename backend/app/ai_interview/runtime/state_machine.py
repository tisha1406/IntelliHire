from typing import Dict, List
from app.ai_interview.core.enums import InterviewState
from app.ai_interview.runtime.exceptions import IllegalStateTransitionError

class StateMachine:
    """
    Deterministic InterviewState transition guard.
    Terminal states are permanent.
    """
    
    # Legal transitions defined as: { from_state: [legal_to_states] }
    # Note: CREATED -> INITIALIZING is handled safely.
    # We do NOT include PLANNING in runtime.
    _LEGAL_TRANSITIONS: Dict[InterviewState, List[InterviewState]] = {
        InterviewState.CREATED: [InterviewState.INITIALIZING, InterviewState.FAILED],
        InterviewState.INITIALIZING: [InterviewState.IN_PROGRESS, InterviewState.FAILED],
        InterviewState.IN_PROGRESS: [InterviewState.PAUSED, InterviewState.COMPLETED, InterviewState.FAILED],
        InterviewState.PAUSED: [InterviewState.IN_PROGRESS, InterviewState.FAILED],
        InterviewState.COMPLETED: [],  # Terminal
        InterviewState.FAILED: [],     # Terminal
    }

    @staticmethod
    def can_transition(from_state: InterviewState, to_state: InterviewState) -> bool:
        """
        Check if a transition is explicitly allowed.
        """
        return to_state in StateMachine._LEGAL_TRANSITIONS.get(from_state, [])

    @staticmethod
    def assert_transition(from_state: InterviewState, to_state: InterviewState) -> None:
        """
        Validate transition or raise IllegalStateTransitionError.
        """
        if not StateMachine.can_transition(from_state, to_state):
            raise IllegalStateTransitionError(
                f"Illegal state transition from {from_state.value} to {to_state.value}"
            )
