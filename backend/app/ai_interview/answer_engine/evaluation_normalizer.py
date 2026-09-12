from typing import List
from app.ai_interview.answer_engine.schemas import RawEvaluation, EvaluationResult, EvaluationRequest

class EvaluationNormalizer:
    """
    Normalizes valid RawEvaluation into the deterministic EvaluationResult.
    Handles score rounding, list deduplication, and bounds limiting.
    """
    
    @staticmethod
    def _deduplicate_and_limit(items: List[str], max_items: int = 5) -> List[str]:
        seen = set()
        result = []
        for item in items:
            clean_item = item.strip()
            if clean_item and clean_item.lower() not in seen:
                seen.add(clean_item.lower())
                result.append(clean_item)
                if len(result) >= max_items:
                    break
        return result

    @staticmethod
    def normalize(evaluation: RawEvaluation, request: EvaluationRequest) -> EvaluationResult:
        
        normalized_scores = {
            "relevance": round(evaluation.relevance_score, 2),
            "correctness": round(evaluation.correctness_score, 2),
            "depth": round(evaluation.depth_score, 2),
            "clarity": round(evaluation.clarity_score, 2)
        }
        
        return EvaluationResult(
            session_id=request.session_id,
            question_record_id=request.question_record_id,
            topic_id=request.topic_id,
            overall_score=round(evaluation.overall_score, 2),
            normalized_dimension_scores=normalized_scores,
            strengths=EvaluationNormalizer._deduplicate_and_limit(evaluation.strengths),
            weaknesses=EvaluationNormalizer._deduplicate_and_limit(evaluation.weaknesses),
            missing_concepts=EvaluationNormalizer._deduplicate_and_limit(evaluation.missing_concepts),
            evidence_summary=evaluation.evidence_summary.strip(),
            follow_up_signal=evaluation.follow_up_signal,
            qualitative_coverage_signal=evaluation.qualitative_coverage_signal
        )
