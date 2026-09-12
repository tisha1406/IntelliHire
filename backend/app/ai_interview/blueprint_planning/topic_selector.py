import re
from typing import List, Dict
from app.ai_interview.blueprint_planning.schemas import BlueprintPlanningRequest
from app.ai_interview.blueprint_planning.enums import TopicSourceCode

class TopicCandidate:
    def __init__(self, name: str):
        self.name = name
        self.sources: List[TopicSourceCode] = []
        self.priority: int = 1
        self.mandatory: bool = False

class TopicSelector:
    @staticmethod
    def select_topics(request: BlueprintPlanningRequest) -> List[TopicCandidate]:
        topic_map: Dict[str, TopicCandidate] = {}
        
        def add_topic(name: str, source: TopicSourceCode):
            if not name.strip():
                return
            # Normalize inner and outer whitespace for the deduplication key
            key = re.sub(r'\s+', ' ', name.lower().strip())
            if key not in topic_map:
                topic_map[key] = TopicCandidate(name=name.strip())
            if source not in topic_map[key].sources:
                topic_map[key].sources.append(source)

        # 1. Role required topics
        for skill in request.job_context.required_skills:
            add_topic(skill, TopicSourceCode.ROLE_REQUIRED)

        # 2. Resume skills
        for skill in request.candidate_context.structured_resume.skills:
            add_topic(skill.name, TopicSourceCode.RESUME_SKILL)
            
        # 3. Resume projects & experience (evidence)
        for proj in request.candidate_context.structured_resume.projects:
            for tech in proj.technologies:
                add_topic(tech, TopicSourceCode.PROJECT_EVIDENCE)
                
        for exp in request.candidate_context.structured_resume.experience:
            # We could extract keywords, for deterministic baseline just use title if nothing else
            add_topic(exp.title, TopicSourceCode.EXPERIENCE_EVIDENCE)
                
        # 4. Mode required topics
        allowed_q_types = request.mode_definition.settings.allowed_question_types
        if allowed_q_types and "behavioral" in allowed_q_types:
             add_topic("Behavioral & Situational", TopicSourceCode.MODE_REQUIRED)
             
        return list(topic_map.values())
