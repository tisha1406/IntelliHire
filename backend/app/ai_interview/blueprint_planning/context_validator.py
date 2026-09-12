from app.ai_interview.resume_processing.enums import ExtractionQualityStatus
from app.ai_interview.blueprint_planning.schemas import BlueprintPlanningRequest
from app.ai_interview.blueprint_planning.exceptions import ContextValidationError

class ContextValidator:
    @staticmethod
    def validate(request: BlueprintPlanningRequest) -> None:
        if request.candidate_context.quality_status == ExtractionQualityStatus.UNUSABLE:
            raise ContextValidationError("Candidate context is UNUSABLE. Cannot plan blueprint.")
        if request.job_context.interview_duration_minutes <= 0:
            raise ContextValidationError("Interview duration must be greater than 0.")
