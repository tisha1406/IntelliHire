import pytest
from app.ai_interview.runtime.topic_progression_engine import TopicProgressionEngine
from app.ai_interview.schemas.session import InterviewSessionSchema, TopicProgress
from app.ai_interview.schemas.blueprint import InterviewBlueprint, TopicBlueprint
from app.ai_interview.core.enums import TopicState, RequirementCriticality, DifficultyLevel

def build_session(topics_progress, topics_blueprint, global_asked=0):
    blueprint = InterviewBlueprint(
        blueprint_version="1.0",
        total_question_budget=10,
        min_questions=1,
        max_questions=10,
        emergency_max_questions=15,
        topics=topics_blueprint
    )
    return InterviewSessionSchema(
        session_id="test",
        candidate_id="cand",
        company_id="comp",
        campaign_id="camp",
        mode_id="official",
        mode_version=1,
        blueprint=blueprint,
        questions_asked_total=global_asked,
        topic_progress=topics_progress,
        created_at="2023-01-01T00:00:00Z"
    )

def test_highest_priority_selected_over_mandatory():
    # Prove that mandatory no longer overrides priority.
    # Topic 1: Mandatory, Criticality PREFERRED (Priority ~1.0)
    # Topic 2: Not mandatory, Criticality CRITICAL (Priority ~1.5)
    
    t1_bp = TopicBlueprint(topic_id="t1", topic_name="T1", source="none", priority=1, mandatory=True, question_budget=2)
    t2_bp = TopicBlueprint(topic_id="t2", topic_name="T2", source="none", priority=2, mandatory=False, question_budget=2)
    
    t1_prog = TopicProgress(topic_id="t1", criticality=RequirementCriticality.PREFERRED)
    t2_prog = TopicProgress(topic_id="t2", criticality=RequirementCriticality.CRITICAL)
    
    session = build_session([t1_prog, t2_prog], [t1_bp, t2_bp])
    
    next_topic = TopicProgressionEngine.get_next_active_topic(session)
    assert next_topic.topic_id == "t2"
    assert getattr(next_topic, "_selected_priority") > 1.0

def test_covered_and_failed_excluded():
    t1_bp = TopicBlueprint(topic_id="t1", topic_name="T1", source="none", priority=1, question_budget=2)
    t2_bp = TopicBlueprint(topic_id="t2", topic_name="T2", source="none", priority=2, question_budget=2)
    t3_bp = TopicBlueprint(topic_id="t3", topic_name="T3", source="none", priority=3, question_budget=2)
    
    t1_prog = TopicProgress(topic_id="t1", state=TopicState.COVERED, structurally_attempted=True, qualitatively_covered=True)
    t2_prog = TopicProgress(topic_id="t2", state=TopicState.FAILED_ABANDONED, structurally_attempted=True, qualitatively_covered=False)
    t3_prog = TopicProgress(topic_id="t3", state=TopicState.NOT_STARTED)
    
    session = build_session([t1_prog, t2_prog, t3_prog], [t1_bp, t2_bp, t3_bp])
    
    next_topic = TopicProgressionEngine.get_next_active_topic(session)
    assert next_topic.topic_id == "t3"

def test_budget_exhausted_excluded():
    t1_bp = TopicBlueprint(topic_id="t1", topic_name="T1", source="none", priority=1, question_budget=2)
    t2_bp = TopicBlueprint(topic_id="t2", topic_name="T2", source="none", priority=2, question_budget=2)
    
    t1_prog = TopicProgress(topic_id="t1", state=TopicState.IN_PROGRESS, questions_asked=2)
    t2_prog = TopicProgress(topic_id="t2", state=TopicState.IN_PROGRESS, questions_asked=1)
    
    session = build_session([t1_prog, t2_prog], [t1_bp, t2_bp])
    
    next_topic = TopicProgressionEngine.get_next_active_topic(session)
    assert next_topic.topic_id == "t2"

def test_current_topic_not_retained_if_lower_priority():
    # Prove stickiness is removed.
    # Topic 1: IN_PROGRESS, but has high coverage/high readiness -> low priority.
    # Topic 2: NOT_STARTED, high criticality -> high priority.
    # Topic 1 is the current_topic_id.
    
    t1_bp = TopicBlueprint(topic_id="t1", topic_name="T1", source="none", priority=1, question_budget=2)
    t2_bp = TopicBlueprint(topic_id="t2", topic_name="T2", source="none", priority=2, question_budget=2)
    
    t1_prog = TopicProgress(topic_id="t1", state=TopicState.IN_PROGRESS, questions_asked=1, coverage_score=0.9, readiness_score=0.9)
    t2_prog = TopicProgress(topic_id="t2", state=TopicState.NOT_STARTED, criticality=RequirementCriticality.CRITICAL, coverage_score=0.0, readiness_score=0.0)
    
    session = build_session([t1_prog, t2_prog], [t1_bp, t2_bp])
    session.current_topic_id = "t1"
    
    next_topic = TopicProgressionEngine.get_next_active_topic(session)
    # Since stickiness is removed, t2 should win because of higher priority
    assert next_topic.topic_id == "t2"

def test_current_topic_retained_if_highest_priority():
    # Prove that the current topic is still selected if it genuinely has the highest priority.
    # Topic 1: IN_PROGRESS, low coverage/low readiness -> high priority.
    # Topic 2: NOT_STARTED, lower priority.
    # Topic 1 is the current_topic_id.
    
    t1_bp = TopicBlueprint(topic_id="t1", topic_name="T1", source="none", priority=1, question_budget=2)
    t2_bp = TopicBlueprint(topic_id="t2", topic_name="T2", source="none", priority=2, question_budget=2)
    
    t1_prog = TopicProgress(topic_id="t1", state=TopicState.IN_PROGRESS, questions_asked=1, criticality=RequirementCriticality.CRITICAL, coverage_score=0.1, readiness_score=0.1)
    t2_prog = TopicProgress(topic_id="t2", state=TopicState.NOT_STARTED, criticality=RequirementCriticality.PREFERRED, coverage_score=0.0, readiness_score=0.0)
    
    session = build_session([t1_prog, t2_prog], [t1_bp, t2_bp])
    session.current_topic_id = "t1"
    
    next_topic = TopicProgressionEngine.get_next_active_topic(session)
    # t1 should win mathematically
    assert next_topic.topic_id == "t1"
