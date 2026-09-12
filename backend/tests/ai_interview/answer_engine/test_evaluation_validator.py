import pytest
from app.ai_interview.answer_engine.evaluation_validator import EvaluationValidator
from app.ai_interview.answer_engine.schemas import RawEvaluation
from app.ai_interview.answer_engine.enums import FollowUpSignal, CoverageSignal
from app.ai_interview.answer_engine.exceptions import EvaluationValidationError

def test_validator_valid():
    raw = RawEvaluation(
        relevance_score=0.5,
        correctness_score=0.5,
        depth_score=0.5,
        clarity_score=0.5,
        overall_score=0.5,
        strengths=[],
        weaknesses=[],
        missing_concepts=[],
        evidence_summary="Test",
        follow_up_signal=FollowUpSignal.NONE,
        qualitative_coverage_signal=CoverageSignal.NOT_COVERED
    )
    EvaluationValidator.validate(raw) # Should not raise

def test_validator_invalid_score_bounds():
    raw = RawEvaluation(
        relevance_score=1.5,
        correctness_score=0.5,
        depth_score=0.5,
        clarity_score=0.5,
        overall_score=0.5,
        strengths=[],
        weaknesses=[],
        missing_concepts=[],
        evidence_summary="Test",
        follow_up_signal=FollowUpSignal.NONE,
        qualitative_coverage_signal=CoverageSignal.NOT_COVERED
    )
    with pytest.raises(EvaluationValidationError, match="out of bounds"):
        EvaluationValidator.validate(raw)
