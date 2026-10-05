import pytest
from app.ai_interview.core.enums import DifficultyLevel, TopicDimension, InterviewEvidence, BehavioralSpecificity
from app.ai_interview.schemas.session import InterviewSessionSchema, TopicProgress
from app.ai_interview.schemas.blueprint import InterviewBlueprint, TopicBlueprint
from app.ai_interview.schemas.strategy import StrategyDefinition, DifficultyPolicy
from app.ai_interview.runtime.adaptive_difficulty_engine import AdaptiveDifficultyEngine

from app.ai_interview.core.enums import TopicSource

@pytest.fixture
def mock_session():
    topic_bp_1 = TopicBlueprint(topic_id="t1", topic_name="T1", question_budget=3, initial_difficulty=DifficultyLevel.MEDIUM, source=TopicSource.REQUIREMENT, priority=1)
    topic_bp_2 = TopicBlueprint(topic_id="t2", topic_name="T2", question_budget=3, initial_difficulty=DifficultyLevel.EASY, source=TopicSource.REQUIREMENT, priority=2)
    
    bp = InterviewBlueprint(
        blueprint_version="1.0",
        total_question_budget=10,
        min_questions=5,
        max_questions=10,
        emergency_max_questions=12,
        topics=[topic_bp_1, topic_bp_2]
    )
    return InterviewSessionSchema(
        session_id="s1",
        candidate_id="c1",
        company_id="co1",
        campaign_id="ca1",
        mode_id="m1",
        mode_version=1,
        blueprint=bp,
        created_at="2025-01-01T00:00:00Z"
    )

def test_behavioral_starts_at_general(mock_session):
    tp = TopicProgress(topic_id="t1", dimension=TopicDimension.BEHAVIORAL)
    strategy = StrategyDefinition(
        strategy_id="st1", name="S", description="", min_questions=1, target_questions=2, max_questions=3,
        max_questions_per_topic=3, max_followups_per_topic=1, strong_threshold=0.8, acceptable_threshold=0.5, weak_threshold=0.2
    )
    AdaptiveDifficultyEngine.initialize_if_needed(mock_session, tp, strategy)
    assert tp.current_specificity == BehavioralSpecificity.GENERAL
    # Difficulty should not be initialized
    assert tp.current_difficulty is None

def test_behavioral_adapts_specificity(mock_session):
    tp = TopicProgress(topic_id="t1", dimension=TopicDimension.BEHAVIORAL)
    strategy = StrategyDefinition(
        strategy_id="st1", name="S", description="", min_questions=1, target_questions=2, max_questions=3,
        max_questions_per_topic=3, max_followups_per_topic=1, strong_threshold=0.8, acceptable_threshold=0.5, weak_threshold=0.2
    )
    
    # 1. NOT_DEMONSTRATED (vague) -> increase specificity
    AdaptiveDifficultyEngine.adapt(mock_session, tp, overall_score=0.4, strategy=strategy, interview_evidence=InterviewEvidence.NOT_DEMONSTRATED)
    assert tp.current_specificity == BehavioralSpecificity.SPECIFIC
    
    # 2. BASIC (some detail) -> move to evidence_required
    AdaptiveDifficultyEngine.adapt(mock_session, tp, overall_score=0.6, strategy=strategy, interview_evidence=InterviewEvidence.BASIC)
    assert tp.current_specificity == BehavioralSpecificity.EVIDENCE_REQUIRED
    
    # 3. STRONG -> stay at evidence_required (caps at max)
    AdaptiveDifficultyEngine.adapt(mock_session, tp, overall_score=0.9, strategy=strategy, interview_evidence=InterviewEvidence.STRONG)
    assert tp.current_specificity == BehavioralSpecificity.EVIDENCE_REQUIRED

def test_global_scope_difficulty(mock_session):
    tp1 = TopicProgress(topic_id="t1", dimension=TopicDimension.TECHNICAL)
    tp2 = TopicProgress(topic_id="t2", dimension=TopicDimension.TECHNICAL)
    
    strategy = StrategyDefinition(
        strategy_id="st1", name="S", description="", min_questions=1, target_questions=2, max_questions=3,
        max_questions_per_topic=3, max_followups_per_topic=1, strong_threshold=0.8, acceptable_threshold=0.5, weak_threshold=0.2,
        difficulty_policy=DifficultyPolicy(scope="global", reset_on_switch=False)
    )
    
    # Topic 1 starts
    AdaptiveDifficultyEngine.handle_topic_switch(mock_session, tp1, None, strategy)
    assert tp1.current_difficulty == DifficultyLevel.MEDIUM
    
    # Topic 1 adapts to HARD
    AdaptiveDifficultyEngine.adapt(mock_session, tp1, overall_score=0.9, strategy=strategy)
    assert tp1.current_difficulty == DifficultyLevel.HARD
    assert mock_session.current_difficulty == DifficultyLevel.HARD
    
    # Switch to Topic 2
    AdaptiveDifficultyEngine.handle_topic_switch(mock_session, tp2, "t1", strategy)
    # Topic 2 inherits HARD from global session
    assert tp2.current_difficulty == DifficultyLevel.HARD

def test_global_scope_with_reset_on_switch(mock_session):
    tp1 = TopicProgress(topic_id="t1", dimension=TopicDimension.TECHNICAL)
    tp2 = TopicProgress(topic_id="t2", dimension=TopicDimension.TECHNICAL)
    
    strategy = StrategyDefinition(
        strategy_id="st1", name="S", description="", min_questions=1, target_questions=2, max_questions=3,
        max_questions_per_topic=3, max_followups_per_topic=1, strong_threshold=0.8, acceptable_threshold=0.5, weak_threshold=0.2,
        difficulty_policy=DifficultyPolicy(scope="global", reset_on_switch=True)
    )
    
    AdaptiveDifficultyEngine.handle_topic_switch(mock_session, tp1, None, strategy)
    AdaptiveDifficultyEngine.adapt(mock_session, tp1, overall_score=0.9, strategy=strategy)
    assert tp1.current_difficulty == DifficultyLevel.HARD
    
    # Switch to Topic 2
    AdaptiveDifficultyEngine.handle_topic_switch(mock_session, tp2, "t1", strategy)
    # Because reset_on_switch is True, it starts at its configured difficulty (EASY) despite global
    assert tp2.current_difficulty == DifficultyLevel.EASY
