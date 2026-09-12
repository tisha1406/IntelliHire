from app.ai_interview.schemas.blueprint import InterviewBlueprint
from app.ai_interview.blueprint_planning.exceptions import BlueprintValidationError

class BlueprintValidator:
    @staticmethod
    def validate(blueprint: InterviewBlueprint) -> None:
        if blueprint.total_question_budget <= 0:
            raise BlueprintValidationError("Total question budget must be > 0")
            
        if blueprint.min_questions > blueprint.total_question_budget:
            raise BlueprintValidationError("Minimum questions cannot exceed total budget")
            
        if blueprint.min_questions > blueprint.max_questions:
            raise BlueprintValidationError("Minimum questions cannot exceed maximum questions")
            
        topic_names = set()
        for topic in blueprint.topics:
            name_lower = topic.topic_name.lower().strip()
            if name_lower in topic_names:
                raise BlueprintValidationError(f"Duplicate topic found: {topic.topic_name}")
            topic_names.add(name_lower)
