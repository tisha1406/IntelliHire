import re
from typing import List, Dict, Optional
from app.ai_interview.blueprint_planning.schemas import BlueprintPlanningRequest
from app.ai_interview.blueprint_planning.enums import TopicSourceCode
from app.ai_interview.core.enums import InterviewType

class TopicCandidate:
    def __init__(self, name: str):
        self.name = name
        self.sources: List[TopicSourceCode] = []
        self.priority: int = 1
        self.mandatory: bool = False
        # D-03: only ever set for a SITUATIONAL_SCENARIO-sourced topic.
        self.scenario_id: Optional[str] = None
        self.scenario_context: Optional[str] = None

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

        # 2. Resume skills (skip for practice mode)
        if request.mode_definition.mode_id != "practice":
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

        # 5. Situational scenario topic (D-03). Added only when the campaign
        # actually requests situational coverage -- a pure Situational/Case
        # interview, or a Mixed interview whose composition gives the
        # situational dimension non-zero weight. This is purely additive: it
        # never removes or alters the Technical/Resume/Behavioral topics
        # selected above.
        needs_situational = (
            request.interview_type == InterviewType.SITUATIONAL_CASE
            or (
                request.interview_type == InterviewType.MIXED
                and request.mixed_composition is not None
                and request.mixed_composition.situational_case > 0
            )
        )
        if needs_situational and request.selected_scenario is not None:
            scenario = request.selected_scenario
            key = re.sub(r'\s+', ' ', scenario.topic_name.lower().strip())
            if key not in topic_map:
                topic_map[key] = TopicCandidate(name=scenario.topic_name.strip())
            candidate = topic_map[key]
            if TopicSourceCode.SITUATIONAL_SCENARIO not in candidate.sources:
                candidate.sources.append(TopicSourceCode.SITUATIONAL_SCENARIO)
            candidate.scenario_id = scenario.scenario_id
            candidate.scenario_context = scenario.scenario_context

        return list(topic_map.values())
