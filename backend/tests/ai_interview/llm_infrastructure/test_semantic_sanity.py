import pytest
from app.ai_interview.answer_engine.schemas import RawEvaluation, CoverageSignal, FollowUpSignal
from app.ai_interview.answer_engine.evaluation_validator import EvaluationValidator
from app.ai_interview.answer_engine.exceptions import EvaluationValidationError

def test_semantic_sanity_rejects_high_score_with_only_weaknesses():
    raw = RawEvaluation(
        relevance_score=0.9,
        correctness_score=0.9,
        depth_score=0.9,
        clarity_score=0.9,
        overall_score=0.9,
        strengths=[],
        weaknesses=["Completely wrong."],
        missing_concepts=["Everything"],
        evidence_summary="Horrible.",
        follow_up_signal=FollowUpSignal.NONE,
        qualitative_coverage_signal=CoverageSignal.NOT_COVERED
    )
    
    with pytest.raises(EvaluationValidationError, match="high overall score"):
        EvaluationValidator.validate(raw)

def test_semantic_sanity_rejects_missing_evidence():
    raw = RawEvaluation(
        relevance_score=0.5,
        correctness_score=0.5,
        depth_score=0.5,
        clarity_score=0.5,
        overall_score=0.5,
        strengths=["Something"],
        weaknesses=[],
        missing_concepts=[],
        evidence_summary="   ", # Empty
        follow_up_signal=FollowUpSignal.NONE,
        qualitative_coverage_signal=CoverageSignal.NOT_COVERED
    )
    
    with pytest.raises(EvaluationValidationError, match="evidence_summary is missing or empty"):
        EvaluationValidator.validate(raw)

def test_semantic_sanity_valid_pass():
    raw = RawEvaluation(
        relevance_score=0.9,
        correctness_score=0.9,
        depth_score=0.9,
        clarity_score=0.9,
        overall_score=0.9,
        strengths=["Excellent logic"],
        weaknesses=[],
        missing_concepts=[],
        evidence_summary="Candidate nailed it.",
        follow_up_signal=FollowUpSignal.NONE,
        qualitative_coverage_signal=CoverageSignal.QUALITATIVELY_COVERED
    )
    
    # Should not raise
    EvaluationValidator.validate(raw)
