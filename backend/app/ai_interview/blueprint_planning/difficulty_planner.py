from app.ai_interview.core.enums import DifficultyLevel
from app.ai_interview.blueprint_planning.schemas import BlueprintPlanningRequest

class DifficultyPlanner:
    @staticmethod
    def determine_initial_difficulty(request: BlueprintPlanningRequest) -> DifficultyLevel:
        """
        Determines difficulty strictly from job/campaign constraints and mode policy.
        Never infers difficulty from candidate resume quality.
        """
        policy = request.mode_definition.settings.difficulty_policy
        if policy == "strict":
            return DifficultyLevel.HARD
        elif policy == "lenient":
            return DifficultyLevel.EASY
        return DifficultyLevel.MEDIUM
