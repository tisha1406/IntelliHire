from typing import Protocol
from app.ai_interview.answer_engine.schemas import EvaluationRequest, RawEvaluation
from app.ai_interview.answer_engine.enums import FollowUpSignal, CoverageSignal

class AnswerEvaluator(Protocol):
    def evaluate(self, request: EvaluationRequest) -> RawEvaluation:
        ...

class FakeAnswerEvaluator:
    """
    Deterministic evaluator for testing.
    Output is strictly driven by the candidate's answer text for predictable testing.
    Does not use random values.
    """
    
    def __init__(self, fail_mode: bool = False, malformed_mode: bool = False):
        self.fail_mode = fail_mode
        self.malformed_mode = malformed_mode
        
    def evaluate(self, request: EvaluationRequest) -> RawEvaluation:
        if self.fail_mode:
            raise RuntimeError("Fake evaluator simulated failure")
            
        answer = request.candidate_answer.lower()
        
        # Test hooks via magic words
        if "malformed" in answer or self.malformed_mode:
            # Return out-of-bounds scores to trigger EvaluationValidator
            return RawEvaluation(
                relevance_score=9.9, # Invalid scale
                correctness_score=-1.0, # Invalid scale
                depth_score=0.5,
                clarity_score=0.5,
                overall_score=0.5,
                strengths=[],
                weaknesses=[],
                missing_concepts=[],
                evidence_summary="Malformed scores.",
                follow_up_signal=FollowUpSignal.NONE,
                qualitative_coverage_signal=CoverageSignal.NOT_COVERED
            )

        if "excellent" in answer or "strong" in answer:
            return RawEvaluation(
                relevance_score=0.9,
                correctness_score=0.9,
                depth_score=0.9,
                clarity_score=0.9,
                overall_score=0.9,
                strengths=["Great explanation", "Clear logic"],
                weaknesses=[],
                missing_concepts=[],
                evidence_summary="Candidate demonstrated deep understanding.",
                follow_up_signal=FollowUpSignal.NONE,
                qualitative_coverage_signal=CoverageSignal.QUALITATIVELY_COVERED
            )
            
        if "weak" in answer or "don't know" in answer:
            return RawEvaluation(
                relevance_score=0.3,
                correctness_score=0.2,
                depth_score=0.2,
                clarity_score=0.4,
                overall_score=0.25,
                strengths=[],
                weaknesses=["Lacks fundamental knowledge", "Unclear"],
                missing_concepts=["Core principles"],
                evidence_summary="Candidate struggled with the basic concepts.",
                follow_up_signal=FollowUpSignal.CLARIFICATION_MAY_HELP,
                qualitative_coverage_signal=CoverageSignal.NOT_COVERED
            )
            
        # Default partial
        return RawEvaluation(
            relevance_score=0.6,
            correctness_score=0.6,
            depth_score=0.5,
            clarity_score=0.6,
            overall_score=0.57,
            strengths=["Got the basic idea"],
            weaknesses=["Missed edge cases"],
            missing_concepts=["Advanced features"],
            evidence_summary="Candidate has partial understanding but lacks depth.",
            follow_up_signal=FollowUpSignal.DEPTH_PROBE_MAY_HELP,
            qualitative_coverage_signal=CoverageSignal.PARTIALLY_COVERED
        )
