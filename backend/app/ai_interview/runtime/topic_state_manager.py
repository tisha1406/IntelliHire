from app.ai_interview.core.enums import TopicState
from app.ai_interview.schemas.session import TopicProgress
from app.ai_interview.runtime.exceptions import IllegalStateTransitionError

class TopicStateManager:
    """
    Safely transitions TopicState respecting Phase 1 invariants.
    FAILED_ABANDONED is resolved but not qualitatively covered.
    COVERED must be structurally and qualitatively met.
    """

    @staticmethod
    def mark_in_progress(progress: TopicProgress) -> None:
        if progress.state == TopicState.NOT_STARTED:
            progress.state = TopicState.IN_PROGRESS
        elif progress.state != TopicState.IN_PROGRESS:
            raise IllegalStateTransitionError(f"Cannot mark IN_PROGRESS from {progress.state}")

    @staticmethod
    def attempt_cover(progress: TopicProgress) -> None:
        """
        Transitions to COVERED only if schema invariants are satisfied.
        Phase 4 DOES NOT automatically trigger this via question counts.
        """
        if progress.state in [TopicState.COVERED, TopicState.FAILED_ABANDONED]:
            raise IllegalStateTransitionError(f"Topic is already resolved: {progress.state}")
            
        if not progress.structurally_attempted or not progress.qualitatively_covered:
            raise IllegalStateTransitionError(
                "Cannot mark COVERED unless both structurally_attempted and qualitatively_covered are True."
            )
        progress.state = TopicState.COVERED

    @staticmethod
    def mark_failed_abandoned(progress: TopicProgress) -> None:
        """
        Transitions to FAILED_ABANDONED.
        Resolves the topic for progression, but it is not qualitatively covered.
        """
        if progress.state in [TopicState.COVERED, TopicState.FAILED_ABANDONED]:
            raise IllegalStateTransitionError(f"Topic is already resolved: {progress.state}")
            
        progress.structurally_attempted = True
        progress.qualitatively_covered = False
        progress.state = TopicState.FAILED_ABANDONED
