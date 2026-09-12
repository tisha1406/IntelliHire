from typing import List
import uuid
from app.ai_interview.core.enums import DifficultyLevel, QuestionType
from app.ai_interview.schemas.blueprint import InterviewBlueprint, TopicBlueprint
from app.ai_interview.blueprint_planning.schemas import BlueprintPlanningRequest
from app.ai_interview.blueprint_planning.topic_selector import TopicCandidate
from app.ai_interview.blueprint_planning.config import BlueprintPlanningConfig
from app.ai_interview.blueprint_planning.exceptions import BlueprintValidationError

class CoveragePlanner:
    @staticmethod
    def plan(
        request: BlueprintPlanningRequest, 
        topics: List[TopicCandidate], 
        initial_difficulty: DifficultyLevel
    ) -> InterviewBlueprint:
        # Determine global budgets
        # Say, 1 question takes roughly 5 minutes.
        duration = request.job_context.interview_duration_minutes
        
        if request.constraints and request.constraints.total_question_budget:
            total_question_budget = request.constraints.total_question_budget
        else:
            total_question_budget = max(1, duration // 5)
        
        # Sort topics by priority descending, then by name for determinism
        topics.sort(key=lambda t: (t.priority, t.name), reverse=True)
        
        # Limit to max topics based on config or constraints
        max_topics = BlueprintPlanningConfig.MAX_TOPICS
        if request.constraints and request.constraints.max_topics:
            max_topics = request.constraints.max_topics
            
        selected_topics = topics[:max_topics]
        
        # Ensure mandatory topics aren't silently truncated
        for t in topics[max_topics:]:
            if t.mandatory:
                raise BlueprintValidationError(f"Cannot truncate mandatory topic: {t.name}")
        
        # Build TopicBlueprints
        blueprint_topics = []
        allowed_q_types_strs = request.mode_definition.settings.allowed_question_types
        if allowed_q_types_strs:
            allowed_q_types = [QuestionType(qt) for qt in allowed_q_types_strs]
        else:
            allowed_q_types = [QuestionType.INITIAL]
        
        for t in selected_topics:
            # Concise structured selection reasons
            source_str = ",".join(sorted([s.value for s in t.sources]))
            tb = TopicBlueprint(
                topic_id=str(uuid.uuid4()),
                topic_name=t.name,
                source=source_str,
                priority=t.priority,
                mandatory=t.mandatory,
                initial_difficulty=initial_difficulty,
                allowed_question_types=allowed_q_types
            )
            blueprint_topics.append(tb)
            
        # Check impossible budgets
        min_questions_required = sum(BlueprintPlanningConfig.MIN_QUESTIONS_PER_TOPIC for tb in blueprint_topics if tb.mandatory)
        
        if min_questions_required > total_question_budget:
            raise BlueprintValidationError(f"Impossible budget: mandatory minimum coverage ({min_questions_required}) exceeds global budget ({total_question_budget})")
            
        blueprint = InterviewBlueprint(
            blueprint_version="1.0",
            total_question_budget=total_question_budget,
            min_questions=min_questions_required,
            max_questions=total_question_budget,
            emergency_max_questions=total_question_budget + 2,
            topics=blueprint_topics
        )
        return blueprint
