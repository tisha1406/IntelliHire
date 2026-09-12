import pytest
from app.ai_interview.answer_engine.evaluation_normalizer import EvaluationNormalizer
from app.ai_interview.answer_engine.schemas import RawEvaluation, EvaluationRequest
from app.ai_interview.answer_engine.enums import FollowUpSignal, CoverageSignal
from app.ai_interview.core.enums import QuestionType, DifficultyLevel

def test_normalizer_deduplicates():
    raw = RawEvaluation(
        relevance_score=0.5111,
        correctness_score=0.5,
        depth_score=0.5,
        clarity_score=0.5,
        overall_score=0.5,
        strengths=["Good", "good", "  Good  ", "Nice"],
        weaknesses=[],
        missing_concepts=[],
        evidence_summary="Test",
        follow_up_signal=FollowUpSignal.NONE,
        qualitative_coverage_signal=CoverageSignal.NOT_COVERED
    )
    req = EvaluationRequest(session_id="s1", question_record_id="q1", topic_id="t1", topic_name="Python", question_text="Q", question_type=QuestionType.INITIAL, difficulty=DifficultyLevel.EASY, candidate_answer="A")
    
    res = EvaluationNormalizer.normalize(raw, req)
    
    # Should deduplicate case-insensitively and strip spaces
    assert res.strengths == ["Good", "Nice"]
    assert res.normalized_dimension_scores["relevance"] == 0.51
