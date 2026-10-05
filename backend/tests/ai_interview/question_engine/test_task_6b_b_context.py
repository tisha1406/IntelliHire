import pytest
from app.ai_interview.core.enums import (
    InterviewType, TopicDimension, QuestionCategory, 
    RequirementCriticality, ResumeEvidence, QuestionType, DifficultyLevel
)
from app.ai_interview.question_engine.question_request_builder import QuestionRequestBuilder
from app.ai_interview.question_engine.schemas import QuestionTurnPlan, QuestionRecord
from app.ai_interview.answer_engine.schemas import EvaluationRecord
from app.ai_interview.answer_engine.enums import CoverageSignal, FollowUpSignal

def test_builder_injects_previous_context(candidate_context, interview_mode):
    # Setup history
    q1 = QuestionRecord.model_construct(
        record_id="q1", session_id="s1", turn_number=1, topic_id="t1",
        question_text="First question?", question_type=QuestionType.INITIAL,
        difficulty=DifficultyLevel.MEDIUM
    )
    q2 = QuestionRecord.model_construct(
        record_id="q2", session_id="s1", turn_number=2, topic_id="t1",
        question_text="Second question?", question_type=QuestionType.INITIAL,
        difficulty=DifficultyLevel.MEDIUM
    )
    
    e1 = EvaluationRecord.model_construct(
        evaluation_id="e1", question_record_id="q1", topic_id="t1",
        overall_score=0.8, correctness=0.9, coverage=0.7, confidence=0.8,
        qualitative_coverage_signal=CoverageSignal.PARTIALLY_COVERED,
        follow_up_signal=FollowUpSignal.NONE, evidence_quality="Good"
    )
    e2 = EvaluationRecord.model_construct(
        evaluation_id="e2", question_record_id="q2", topic_id="t1",
        overall_score=0.4, correctness=0.3, coverage=0.5, confidence=0.9,
        qualitative_coverage_signal=CoverageSignal.NOT_COVERED,
        follow_up_signal=FollowUpSignal.NONE, evidence_quality="Poor"
    )
    
    question_history = [q1, q2]
    evaluation_history = [e1, e2]

    # Plan for a follow-up question
    plan = QuestionTurnPlan(
        session_id="s1", topic_id="t1", topic_name="Docker", difficulty=DifficultyLevel.MEDIUM,
        allowed_question_types=[QuestionType.FOLLOW_UP], topic_question_budget=3, topic_questions_asked=2,
        total_question_budget=10, total_questions_asked=2, turn_number=3, allowed=True,
        category=QuestionCategory.FOLLOWUP_DEPTH
    )
    
    req = QuestionRequestBuilder.build(
        plan, candidate_context, interview_mode, 
        question_history=question_history, evaluation_history=evaluation_history
    )
    
    # Assertions
    assert req.previous_question_for_followup == "Second question?"
    assert req.previous_answer is None  # Reported as missing from schema
    assert req.previous_evaluation is not None
    assert req.previous_evaluation["score"] == 0.4
    assert req.previous_evaluation["evidence_quality"] == "Poor"
    # Ensure no leaked other evaluation
    assert req.previous_evaluation["score"] != 0.8
    # Previous questions list should still have both for duplicate avoidance
    assert len(req.previous_questions) == 2

def test_builder_no_context_for_new_category(candidate_context, interview_mode):
    # Even if history exists, NEW category should not extract previous_question_for_followup
    q1 = QuestionRecord.model_construct(
        record_id="q1", session_id="s1", turn_number=1, topic_id="t1",
        question_text="First question?", question_type=QuestionType.INITIAL,
        difficulty=DifficultyLevel.MEDIUM
    )
    e1 = EvaluationRecord.model_construct(
        evaluation_id="e1", question_record_id="q1", topic_id="t1",
        overall_score=0.8, qualitative_coverage_signal=CoverageSignal.PARTIALLY_COVERED,
        follow_up_signal=FollowUpSignal.NONE
    )
    
    plan = QuestionTurnPlan(
        session_id="s1", topic_id="t2", topic_name="K8s", difficulty=DifficultyLevel.MEDIUM,
        allowed_question_types=[QuestionType.INITIAL], topic_question_budget=3, topic_questions_asked=0,
        total_question_budget=10, total_questions_asked=1, turn_number=2, allowed=True,
        category=QuestionCategory.NEW
    )
    
    req = QuestionRequestBuilder.build(
        plan, candidate_context, interview_mode, 
        question_history=[q1], evaluation_history=[e1]
    )
    
    assert req.previous_question_for_followup is None
    assert req.previous_evaluation is None
