from typing import List
from app.ai_interview.blueprint_planning.topic_selector import TopicCandidate
from app.ai_interview.blueprint_planning.enums import TopicSourceCode

class PriorityAllocator:
    @staticmethod
    def allocate(topics: List[TopicCandidate]) -> None:
        """
        Deterministically allocates priority and mandatory flags.
        Priority scale: 1 (Lowest) to 5 (Highest).
        Decisions are fully based on structured sources without opaque scoring.
        Mandatory topics receive a minimum guaranteed priority (>= 4).
        """
        for topic in topics:
            priority = 1
            mandatory = False
            
            # Base priority on evidence type
            if TopicSourceCode.RESUME_SKILL in topic.sources:
                priority = max(priority, 2)
                
            if TopicSourceCode.PROJECT_EVIDENCE in topic.sources or TopicSourceCode.EXPERIENCE_EVIDENCE in topic.sources:
                priority = max(priority, 3)
            
            # Role requirements and Mode requirements trump candidate-only evidence
            if TopicSourceCode.ROLE_REQUIRED in topic.sources:
                priority = max(priority, 4)
                mandatory = True
            
            if TopicSourceCode.MODE_REQUIRED in topic.sources:
                priority = max(priority, 5)
                mandatory = True
                
            topic.priority = priority
            topic.mandatory = mandatory
