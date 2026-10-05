import pytest
from app.ai_interview.schemas.session import InterviewSessionSchema, TopicProgress
from app.ai_interview.core.enums import (
    RequirementCriticality, ResumeEvidence, TopicDimension, InterviewType, TopicState
)
from app.ai_interview.schemas.strategy import MixedComposition
from app.ai_interview.runtime.shadow_priority_calculator import ShadowPriorityCalculator, TopicPriorityResult

def create_topic(topic_id="t1", criticality=None, resume_evidence=None, dimension=None, readiness=0.0, coverage=0.0):
    return TopicProgress(
        topic_id=topic_id,
        criticality=criticality,
        resume_evidence=resume_evidence,
        dimension=dimension,
        readiness_score=readiness,
        coverage_score=coverage,
        structurally_attempted=False,
        qualitatively_covered=False
    )

from datetime import datetime, timezone
def create_session(interview_type=InterviewType.TECHNICAL, mixed_composition=None, mode_id="official"):
    session = InterviewSessionSchema(
        session_id="s1",
        company_id="c1",
        candidate_id="c1",
        campaign_id="camp1",
        mode_id=mode_id,
        mode_version=1,
        interview_type=interview_type,
        mixed_composition=mixed_composition,
        blueprint={
            "blueprint_version": "1.0",
            "total_question_budget": 10,
            "min_questions": 5,
            "max_questions": 15,
            "emergency_max_questions": 20,
            "topics": []
        },
        created_at=datetime.now(timezone.utc)
    )
    return session

def test_1_critical_multiplier():
    t = create_topic(criticality=RequirementCriticality.CRITICAL)
    s = create_session()
    res = ShadowPriorityCalculator.calculate_priority(s, t)
    assert res.criticality_multiplier == 1.5

def test_2_required_multiplier():
    t = create_topic(criticality=RequirementCriticality.REQUIRED)
    s = create_session()
    res = ShadowPriorityCalculator.calculate_priority(s, t)
    assert res.criticality_multiplier == 1.2

def test_3_preferred_multiplier():
    t = create_topic(criticality=RequirementCriticality.PREFERRED)
    s = create_session()
    res = ShadowPriorityCalculator.calculate_priority(s, t)
    assert res.criticality_multiplier == 1.0

def test_4_resume_only_multiplier():
    t = create_topic(criticality=RequirementCriticality.RESUME_ONLY)
    s = create_session()
    res = ShadowPriorityCalculator.calculate_priority(s, t)
    assert res.criticality_multiplier == 0.7

def test_5_absent_resume():
    t = create_topic(resume_evidence=ResumeEvidence.ABSENT)
    s = create_session()
    res = ShadowPriorityCalculator.calculate_priority(s, t)
    assert res.resume_evidence_score == 0.0

def test_6_partial_resume():
    t = create_topic(resume_evidence=ResumeEvidence.PARTIAL)
    s = create_session()
    res = ShadowPriorityCalculator.calculate_priority(s, t)
    assert res.resume_evidence_score == 0.5

def test_7_strong_resume():
    t = create_topic(resume_evidence=ResumeEvidence.STRONG)
    s = create_session()
    res = ShadowPriorityCalculator.calculate_priority(s, t)
    assert res.resume_evidence_score == 1.0

def test_8_non_mixed_composition():
    t = create_topic(dimension=TopicDimension.TECHNICAL)
    s = create_session(interview_type=InterviewType.TECHNICAL)
    res = ShadowPriorityCalculator.calculate_priority(s, t)
    assert res.composition_score == 0.0

def test_9_mixed_composition():
    t = create_topic(dimension=TopicDimension.TECHNICAL)
    mixed = MixedComposition(technical=0.4, resume_experience=0.25, hr_behavioral=0.2, situational_case=0.15)
    s = create_session(interview_type=InterviewType.MIXED, mixed_composition=mixed)
    res = ShadowPriorityCalculator.calculate_priority(s, t)
    assert res.composition_score == 0.4

def test_10_coverage():
    t1 = create_topic(coverage=0.1)
    t2 = create_topic(coverage=0.9)
    s = create_session()
    res1 = ShadowPriorityCalculator.calculate_priority(s, t1)
    res2 = ShadowPriorityCalculator.calculate_priority(s, t2)
    # Lower coverage -> higher priority (all else equal)
    assert res1.priority > res2.priority

def test_11_performance():
    t1 = create_topic(readiness=0.2) # weak performance -> inverse_confidence 0.8
    t2 = create_topic(readiness=0.8) # strong performance -> inverse_confidence 0.2
    s = create_session()
    res1 = ShadowPriorityCalculator.calculate_priority(s, t1)
    res2 = ShadowPriorityCalculator.calculate_priority(s, t2)
    # Weak performance -> higher priority
    assert res1.priority > res2.priority

def test_12_identical_inputs():
    t1 = create_topic(coverage=0.5, readiness=0.5)
    t2 = create_topic(coverage=0.5, readiness=0.5)
    s = create_session()
    res1 = ShadowPriorityCalculator.calculate_priority(s, t1)
    res2 = ShadowPriorityCalculator.calculate_priority(s, t2)
    assert res1.priority == res2.priority

def test_13_deterministic_tie_break():
    # priority, criticality, coverage are equal
    t1 = create_topic(topic_id="z_topic", criticality=RequirementCriticality.PREFERRED)
    t2 = create_topic(topic_id="a_topic", criticality=RequirementCriticality.PREFERRED)
    s = create_session()
    # lexical ordering means "a_topic" beats "z_topic"
    winner = ShadowPriorityCalculator.get_best_topic(s, [t1, t2])
    assert winner.topic_id == "a_topic"
    
    # Switch order
    winner2 = ShadowPriorityCalculator.get_best_topic(s, [t2, t1])
    assert winner2.topic_id == "a_topic"

def test_14_critical_outranks_preferred():
    t1 = create_topic(topic_id="pref", criticality=RequirementCriticality.PREFERRED)
    t2 = create_topic(topic_id="crit", criticality=RequirementCriticality.CRITICAL)
    s = create_session()
    winner = ShadowPriorityCalculator.get_best_topic(s, [t1, t2])
    assert winner.topic_id == "crit"

def test_15_resume_only_does_not_outrank_required_automatically():
    # Resume-only with STRONG resume evidence (base score increases)
    t_resume_only = create_topic(topic_id="res", criticality=RequirementCriticality.RESUME_ONLY, resume_evidence=ResumeEvidence.STRONG)
    # Required with ABSENT resume evidence
    t_required = create_topic(topic_id="req", criticality=RequirementCriticality.REQUIRED, resume_evidence=ResumeEvidence.ABSENT)
    
    s = create_session()
    res1 = ShadowPriorityCalculator.calculate_priority(s, t_resume_only)
    res2 = ShadowPriorityCalculator.calculate_priority(s, t_required)
    
    # Let's see the base terms:
    # res1: base = 1.0 (resume) + 1.0 (inverse_conf) + 1.0 (coverage term 1-0) = 3.0. mult = 0.7 -> priority 2.1
    # res2: base = 0.0 + 1.0 + 1.0 = 2.0. mult = 1.2 -> priority 2.4
    # Required wins.
    assert res2.priority > res1.priority

def test_18_old_campaign_no_strategy_snapshot():
    # Session without mixed_composition set
    s = create_session()
    # explicitly remove field to simulate old data struct
    delattr(s, "mixed_composition")
    t = create_topic()
    res = ShadowPriorityCalculator.calculate_priority(s, t)
    assert res is not None

