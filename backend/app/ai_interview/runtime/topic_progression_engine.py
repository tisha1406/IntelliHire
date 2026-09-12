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
        
        # Filter unresolved topics
        unresolved = []
        for p in session.topic_progress:
            if p.state not in [TopicState.COVERED, TopicState.FAILED_ABANDONED]:
                unresolved.append(p)
                
        if not unresolved:
            return None
            
        # Helper to get sorting keys (mandatory True first, then priority desc, then blueprint index ascending)
        blueprint_order = {t.topic_id: i for i, t in enumerate(session.blueprint.topics)}
        
        def sort_key(progress: TopicProgress):
            bp_topic = blueprint_map[progress.topic_id]
            # mandatory -> boolean (True > False), we negate boolean for ascending sort
            return (not bp_topic.mandatory, -bp_topic.priority, blueprint_order[progress.topic_id])
            
        unresolved.sort(key=sort_key)
        return unresolved[0]
