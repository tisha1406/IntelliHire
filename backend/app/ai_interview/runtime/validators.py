from app.ai_interview.schemas.session import InterviewSessionSchema
from app.ai_interview.runtime.exceptions import RuntimeInvariantError
from app.ai_interview.core.enums import InterviewState

class Validators:
    @staticmethod
    def validate_session(session: InterviewSessionSchema) -> None:
        """
        Deterministic runtime invariant validation.
        """
        # Blueprint immutability implicitly maintained by not offering mutation methods,
        # but we can verify topic progress maps correctly.
        blueprint_ids = {t.topic_id for t in session.blueprint.topics}
        progress_ids = set()
        
        for prog in session.topic_progress:
            if prog.topic_id not in blueprint_ids:
                raise RuntimeInvariantError(f"TopicProgress ID {prog.topic_id} not found in blueprint.")
            if prog.topic_id in progress_ids:
                raise RuntimeInvariantError(f"Duplicate TopicProgress found for {prog.topic_id}.")
            progress_ids.add(prog.topic_id)
            
            # Counter sanity
            if prog.follow_up_count < 0:
                raise RuntimeInvariantError(f"Topic follow_up_count cannot be negative for {prog.topic_id}")
            if prog.questions_asked < 0:
                raise RuntimeInvariantError(f"Topic questions_asked cannot be negative for {prog.topic_id}")
                
        if session.questions_asked_total < 0:
            raise RuntimeInvariantError("Total questions asked cannot be negative.")
            
        # Terminal state progression check
        if session.state in [InterviewState.COMPLETED, InterviewState.FAILED]:
            # Runtime should not be "active"
            pass 
