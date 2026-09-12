from app.ai_interview.schemas.blueprint import InterviewBlueprint
from app.ai_interview.blueprint_planning.schemas import BlueprintPlanningRequest
from app.ai_interview.blueprint_planning.context_validator import ContextValidator
from app.ai_interview.blueprint_planning.topic_selector import TopicSelector
from app.ai_interview.blueprint_planning.priority_allocator import PriorityAllocator
from app.ai_interview.blueprint_planning.difficulty_planner import DifficultyPlanner
from app.ai_interview.blueprint_planning.coverage_planner import CoveragePlanner
from app.ai_interview.blueprint_planning.blueprint_validator import BlueprintValidator

class InterviewBlueprintPlanner:
    def plan(self, request: BlueprintPlanningRequest) -> InterviewBlueprint:
        # 1. Validate Input Contexts
        ContextValidator.validate(request)
        
        # 2. Topic Selection
        topics = TopicSelector.select_topics(request)
        
        # 3. Priority Allocation
        PriorityAllocator.allocate(topics)
        
        # 4. Difficulty Planning
        initial_difficulty = DifficultyPlanner.determine_initial_difficulty(request)
        
        # 5. Coverage Planning & Blueprint Assembly
        blueprint = CoveragePlanner.plan(request, topics, initial_difficulty)
        
        # 6. Blueprint Validation
        BlueprintValidator.validate(blueprint)
        
        return blueprint
