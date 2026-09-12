from app.ai_interview.answer_engine.schemas import RawEvaluation
from app.ai_interview.answer_engine.exceptions import EvaluationValidationError

class EvaluationValidator:
    """
    Validates the structure and bounds of the RawEvaluation.
    Ensures LLM hallucinations don't corrupt downstream logic.
    """
    
    @staticmethod
    def validate(evaluation: RawEvaluation) -> None:
        # Validate scores are between 0.0 and 1.0
        scores = {
            "relevance_score": evaluation.relevance_score,
            "correctness_score": evaluation.correctness_score,
            "depth_score": evaluation.depth_score,
            "clarity_score": evaluation.clarity_score,
            "overall_score": evaluation.overall_score
        }
        
        for name, value in scores.items():
            if not isinstance(value, (int, float)):
                raise EvaluationValidationError(f"{name} must be numeric, got {type(value)}")
            if value < 0.0 or value > 1.0:
                raise EvaluationValidationError(f"{name} is out of bounds [0.0, 1.0]: {value}")
                
        # Basic list validation
        if not isinstance(evaluation.strengths, list):
            raise EvaluationValidationError("strengths must be a list")
        if not isinstance(evaluation.weaknesses, list):
            raise EvaluationValidationError("weaknesses must be a list")
        if not isinstance(evaluation.missing_concepts, list):
            raise EvaluationValidationError("missing_concepts must be a list")

        # Semantic Sanity Validation
        if evaluation.overall_score >= 0.8:
            if not evaluation.strengths and evaluation.weaknesses:
                raise EvaluationValidationError("Contradictory output: high overall score (>= 0.8) requires at least one strength if weaknesses are provided.")
                
        if not evaluation.evidence_summary or not evaluation.evidence_summary.strip():
            raise EvaluationValidationError("Contradictory output: evidence_summary is missing or empty.")
