import pytest
from app.ai_interview.answer_engine.coverage_assessor import CoverageAssessor
from app.ai_interview.schemas.session import TopicEvaluationAggregate, TopicProgress
from app.ai_interview.answer_engine.schemas import EvaluationResult
from app.ai_interview.answer_engine.enums import CoverageSignal, FollowUpSignal
from app.ai_interview.core.enums import TopicState

def test_coverage_assessor_minimum_questions():
    agg = TopicEvaluationAggregate(answers_evaluated=0)
    prog = TopicProgress(topic_id="t1", questions_asked=0)
    eval_res = EvaluationResult(session_id="s1", question_record_id="q1", topic_id="t1", overall_score=0.9, follow_up_signal=FollowUpSignal.NONE, qualitative_coverage_signal=CoverageSignal.QUALITATIVELY_COVERED, evidence_summary="")
    
    # Even if LLM says covered, questions_asked < 1 (from config) so should be False
    assessment = CoverageAssessor.assess(agg, eval_res, prog, topic_budget=5)
    assert not assessment.is_covered

def test_coverage_assessor_budget_exhausted_success():
    agg = TopicEvaluationAggregate(answers_evaluated=4, cumulative_score=2.0)
    prog = TopicProgress(topic_id="t1", questions_asked=5)
    eval_res = EvaluationResult(session_id="s1", question_record_id="q5", topic_id="t1", overall_score=0.9, follow_up_signal=FollowUpSignal.NONE, qualitative_coverage_signal=CoverageSignal.PARTIALLY_COVERED, evidence_summary="")
    
    assessment = CoverageAssessor.assess(agg, eval_res, prog, topic_budget=5)
    # Average will be 2.9 / 5 = 0.58 >= 0.5 -> Covered
    assert assessment.is_covered

def test_coverage_assessor_budget_exhausted_fail():
    agg = TopicEvaluationAggregate(answers_evaluated=4, cumulative_score=1.0)
    prog = TopicProgress(topic_id="t1", questions_asked=5)
    eval_res = EvaluationResult(session_id="s1", question_record_id="q5", topic_id="t1", overall_score=0.1, follow_up_signal=FollowUpSignal.NONE, qualitative_coverage_signal=CoverageSignal.PARTIALLY_COVERED, evidence_summary="")
    
    assessment = CoverageAssessor.assess(agg, eval_res, prog, topic_budget=5)
    # Average 1.1 / 5 = 0.22 < 0.5 -> Not Covered
    assert not assessment.is_covered

def test_coverage_assessor_early_coverage_protection():
    agg = TopicEvaluationAggregate(answers_evaluated=1, strong_answers=1, cumulative_score=0.9)
    prog = TopicProgress(topic_id="t1", questions_asked=2)
    eval_res = EvaluationResult(session_id="s1", question_record_id="q2", topic_id="t1", overall_score=0.9, follow_up_signal=FollowUpSignal.NONE, qualitative_coverage_signal=CoverageSignal.QUALITATIVELY_COVERED, evidence_summary="")
    
    assessment = CoverageAssessor.assess(agg, eval_res, prog, topic_budget=5)
    # 2 strong answers -> Covered
    assert assessment.is_covered
