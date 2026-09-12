import pytest
from app.ai_interview.answer_engine.coverage_assessor import CoverageAssessor
from app.ai_interview.schemas.session import TopicEvaluationAggregate, TopicProgress
from app.ai_interview.answer_engine.schemas import EvaluationResult
from app.ai_interview.answer_engine.enums import CoverageSignal, FollowUpSignal
from app.ai_interview.core.enums import TopicState

def test_llm_defanging_premature_coverage_rejected():
    agg = TopicEvaluationAggregate(answers_evaluated=0, cumulative_score=0)
    prog = TopicProgress(topic_id="t1", questions_asked=1)
    
    # LLM hallucinates that a single weak answer perfectly covers the topic
    eval_res = EvaluationResult(
        session_id="s1", question_record_id="q1", topic_id="t1",
        overall_score=0.2, # Very weak
        follow_up_signal=FollowUpSignal.NONE,
        qualitative_coverage_signal=CoverageSignal.QUALITATIVELY_COVERED, # LLM hallucination!
        evidence_summary=""
    )
    
    assessment = CoverageAssessor.assess(agg, eval_res, prog, topic_budget=5)
    
    # Deterministic layer MUST override LLM coverage because budget condition / score is not met
    assert assessment.is_covered is False

def test_llm_defanging_contradictory_signals():
    agg = TopicEvaluationAggregate(answers_evaluated=4, cumulative_score=0)
    prog = TopicProgress(topic_id="t1", questions_asked=5)
    
    # LLM hallucinates full coverage but gives 0 score
    eval_res = EvaluationResult(
        session_id="s1", question_record_id="q5", topic_id="t1",
        overall_score=0.0,
        follow_up_signal=FollowUpSignal.NONE,
        qualitative_coverage_signal=CoverageSignal.QUALITATIVELY_COVERED, # Contradictory
        evidence_summary=""
    )
    
    assessment = CoverageAssessor.assess(agg, eval_res, prog, topic_budget=5)
    
    # Avg score will be 0 / 5 = 0. deterministic threshold requires >= 0.5 for exhausted budget coverage
    assert assessment.is_covered is False
