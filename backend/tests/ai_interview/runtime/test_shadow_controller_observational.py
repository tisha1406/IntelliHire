import pytest
from app.ai_interview.schemas.session import InterviewSessionSchema, TopicProgress
from app.ai_interview.core.enums import (
    RequirementCriticality, ResumeEvidence, TopicDimension, InterviewType, InterviewState
)
from app.ai_interview.runtime.enums import RuntimeAction
from app.ai_interview.schemas.strategy import MixedComposition
from app.ai_interview.schemas.blueprint import InterviewBlueprint, TopicBlueprint
from app.ai_interview.runtime.runtime_controller import RuntimeController, RuntimeDecision
from datetime import datetime, timezone

def create_mock_session(mode_id="official"):
    # Create two topics:
    # Topic A: mandatory, priority 1
    # Topic B: optional, priority 5
    
    blueprint = InterviewBlueprint(
        blueprint_version="1.0",
        total_question_budget=10,
        min_questions=5,
        max_questions=15,
        emergency_max_questions=20,
        topics=[
            TopicBlueprint(
                topic_id="topic_a",
                topic_name="Topic A",
                dimension=TopicDimension.TECHNICAL,
                source="requirement",
                priority=1,
                mandatory=True
            ),
            TopicBlueprint(
                topic_id="topic_b",
                topic_name="Topic B",
                dimension=TopicDimension.TECHNICAL,
                source="resume",
                priority=5,
                mandatory=False
            )
        ]
    )
    
    # Topic A has no resume evidence, covered = 0.9 (almost covered). High coverage -> low shadow priority.
    # Topic B has strong resume evidence, covered = 0.1 (low coverage). Low coverage -> high shadow priority.
    # TopicProgressionEngine (old engine) selects mandatory topics first, so it will select Topic A.
    # ShadowPriorityCalculator should select Topic B (due to strong resume + low coverage).
    
    prog_a = TopicProgress(
        topic_id="topic_a",
        dimension=TopicDimension.TECHNICAL,
        criticality=RequirementCriticality.REQUIRED,
        resume_evidence=ResumeEvidence.ABSENT,
        coverage_score=0.9,
        readiness_score=0.9
    )
    
    prog_b = TopicProgress(
        topic_id="topic_b",
        dimension=TopicDimension.TECHNICAL,
        criticality=RequirementCriticality.PREFERRED,
        resume_evidence=ResumeEvidence.STRONG,
        coverage_score=0.1,
        readiness_score=0.1
    )
    
    session = InterviewSessionSchema(
        session_id="s_shadow",
        company_id="c1",
        candidate_id="c1",
        campaign_id="camp1",
        mode_id=mode_id,
        mode_version=1,
        interview_type=InterviewType.TECHNICAL,
        state=InterviewState.IN_PROGRESS,
        blueprint=blueprint,
        topic_progress=[prog_a, prog_b],
        created_at=datetime.now(timezone.utc)
    )
    return session

def test_17_shadow_mode_now_modifies_selection():
    session = create_mock_session()
    
    from app.ai_interview.runtime.shadow_priority_calculator import ShadowPriorityCalculator
    from app.ai_interview.core.enums import TopicState
    unresolved = [p for p in session.topic_progress if p.state not in [TopicState.COVERED, TopicState.FAILED_ABANDONED]]
    
    winner = ShadowPriorityCalculator.get_best_topic(session, unresolved)
    assert winner.topic_id == "topic_b"
    
    decision = RuntimeController.get_allowed_action(session)
    
    assert decision.allowed_action == RuntimeAction.ADVANCE_TOPIC
    assert decision.active_topic_id == "topic_b"
    assert decision.active_topic_id == winner.topic_id

def test_16_practice_mode_protection(caplog):
    import logging
    caplog.set_level(logging.INFO)
    session = create_mock_session(mode_id="practice")
    
    # Run the controller
    decision = RuntimeController.get_allowed_action(session)
    
    # It still picks topic A
    assert decision.active_topic_id == "topic_a"
    
    # Check that shadow priority was skipped
    assert any("SHADOW_PRIORITY_SKIPPED" in record.message for record in caplog.records)
