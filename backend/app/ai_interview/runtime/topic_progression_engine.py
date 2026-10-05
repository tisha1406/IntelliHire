from typing import Optional, List
from app.ai_interview.schemas.session import InterviewSessionSchema, TopicProgress
from app.ai_interview.core.enums import TopicState

class TopicProgressionEngine:
    """
    Deterministic topic selection engine.
    Selection rules:
    1. Unresolved Mandatory topics
    2. Unresolved Optional topics
    (Sorted by priority descending, then stable blueprint order).
    
    A topic is considered resolved if it is COVERED or FAILED_ABANDONED.
    """
    @staticmethod
    def get_next_active_topic(session: InterviewSessionSchema) -> Optional[TopicProgress]:
        blueprint_map = {t.topic_id: t for t in session.blueprint.topics}
        
        # Filter unresolved topics that haven't exhausted their budget
        unresolved = []
        
        for p in session.topic_progress:
            if p.state not in [TopicState.COVERED, TopicState.FAILED_ABANDONED]:
                bp_topic = blueprint_map.get(p.topic_id)
                budget = bp_topic.question_budget if bp_topic else float('inf')
                if p.questions_asked < budget:
                    unresolved.append(p)
                
        if not unresolved:
            return None
            
        # Cutover: Shadow priority becomes authoritative
        from app.ai_interview.runtime.shadow_priority_calculator import ShadowPriorityCalculator
        best_result = ShadowPriorityCalculator.get_best_topic(session, unresolved)
        
        if best_result:
            # We return the actual TopicProgress object
            for p in session.topic_progress:
                if p.topic_id == best_result.topic_id:
                    # Attach the calculated priority to the returned progress temporarily
                    # so RuntimeController can log it
                    setattr(p, "_selected_priority", best_result.priority)
                    return p
                    
        return None
