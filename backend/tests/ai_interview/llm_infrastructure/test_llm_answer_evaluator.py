import pytest
from app.ai_interview.core.enums import DifficultyLevel, QuestionType
from app.ai_interview.answer_engine.enums import FollowUpSignal
from app.ai_interview.answer_engine.schemas import EvaluationRequest, RawEvaluation, CoverageSignal
from app.ai_interview.answer_engine.llm_answer_evaluator import LLMAnswerEvaluator

class MockSuccessProvider:
    def generate_structured(self, system_prompt, user_prompt, response_model, **kwargs):
        return RawEvaluation(
            relevance_score=0.8,
            correctness_score=0.9,
            depth_score=0.8,
            clarity_score=0.9,
            overall_score=0.85,
            strengths=["Good"],
            weaknesses=[],
            evidence_summary="Good job",
            qualitative_coverage_signal=CoverageSignal.PARTIALLY_COVERED,
            follow_up_signal=FollowUpSignal.NONE
        )
        
    def generate_text(self, *args, **kwargs):
        return "mock text"


def test_llm_answer_evaluator_success_path():
    provider = MockSuccessProvider()
    evaluator = LLMAnswerEvaluator(provider=provider)
    
    req = EvaluationRequest(
        session_id="s1",
        question_record_id="q1",
        topic_id="t1",
        topic_name="Python",
        question_text="What is it?",
        question_type=QuestionType.INITIAL,
        difficulty=DifficultyLevel.EASY,
        candidate_answer="A language.",
        interview_mode_criteria={"technical": "must be correct"},
        relevant_candidate_context=[]
    )
    
    res = evaluator.evaluate(req)
    assert res.overall_score == 0.85
    assert res.qualitative_coverage_signal == CoverageSignal.PARTIALLY_COVERED
