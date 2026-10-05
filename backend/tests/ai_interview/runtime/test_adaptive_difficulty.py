import pytest
from app.ai_interview.runtime.adaptive_difficulty_engine import AdaptiveDifficultyEngine
from app.ai_interview.schemas.session import InterviewSessionSchema, TopicProgress
from app.ai_interview.schemas.strategy import StrategyDefinition, DifficultyPolicy, CompanyOverrideBounds
from app.ai_interview.schemas.blueprint import InterviewBlueprint, TopicBlueprint
from app.ai_interview.core.enums import DifficultyLevel, TopicState

def build_test_state(initial_diff=DifficultyLevel.MEDIUM, current_diff=None, adapts=True, band=None):
    topic_bp = TopicBlueprint(topic_id="t1", topic_name="T1", source="none", priority=1, initial_difficulty=initial_diff)
    blueprint = InterviewBlueprint(
        blueprint_version="1.0",
        total_question_budget=10,
        min_questions=1,
        max_questions=10,
        emergency_max_questions=15,
        topics=[topic_bp]
    )
    
    tp = TopicProgress(topic_id="t1", state=TopicState.IN_PROGRESS, current_difficulty=current_diff)
    
    bounds = CompanyOverrideBounds(allowed_difficulty_bands=band or [])
    policy = DifficultyPolicy(adapts=adapts, step_size=1, band_constrainable=bool(band))
    
    strategy = StrategyDefinition(
        strategy_id="strat",
        name="test",
        description="test",
        min_questions=1,
        target_questions=5,
        max_questions=10,
        max_questions_per_topic=3,
        max_followups_per_topic=2,
        strong_threshold=0.8,
        acceptable_threshold=0.5,
        weak_threshold=0.3,
        difficulty_policy=policy,
        company_override_bounds=bounds
    )
    
    session = InterviewSessionSchema(
        session_id="s",
        candidate_id="c",
        company_id="c",
        campaign_id="c",
        mode_id="official",
        mode_version=1,
        blueprint=blueprint,
        topic_progress=[tp],
        created_at="2023-01-01T00:00:00Z"
    )
    
    return session, tp, strategy

def test_easy_plus_strong_goes_to_medium():
    session, tp, strategy = build_test_state(initial_diff=DifficultyLevel.EASY)
    AdaptiveDifficultyEngine.adapt(session, tp, 0.9, strategy)
    assert tp.current_difficulty == DifficultyLevel.MEDIUM
    
def test_medium_plus_strong_goes_to_hard():
    session, tp, strategy = build_test_state(initial_diff=DifficultyLevel.MEDIUM)
    AdaptiveDifficultyEngine.adapt(session, tp, 0.9, strategy)
    assert tp.current_difficulty == DifficultyLevel.HARD
    
def test_hard_plus_strong_stays_hard():
    session, tp, strategy = build_test_state(initial_diff=DifficultyLevel.HARD)
    AdaptiveDifficultyEngine.adapt(session, tp, 0.9, strategy)
    assert tp.current_difficulty == DifficultyLevel.HARD
    
def test_hard_plus_weak_goes_to_medium():
    session, tp, strategy = build_test_state(initial_diff=DifficultyLevel.HARD)
    AdaptiveDifficultyEngine.adapt(session, tp, 0.2, strategy)
    assert tp.current_difficulty == DifficultyLevel.MEDIUM
    
def test_medium_plus_weak_goes_to_easy():
    session, tp, strategy = build_test_state(initial_diff=DifficultyLevel.MEDIUM)
    AdaptiveDifficultyEngine.adapt(session, tp, 0.2, strategy)
    assert tp.current_difficulty == DifficultyLevel.EASY

def test_easy_plus_weak_stays_easy():
    session, tp, strategy = build_test_state(initial_diff=DifficultyLevel.EASY)
    AdaptiveDifficultyEngine.adapt(session, tp, 0.2, strategy)
    assert tp.current_difficulty == DifficultyLevel.EASY
    
def test_acceptable_stays_unchanged():
    session, tp, strategy = build_test_state(initial_diff=DifficultyLevel.MEDIUM)
    AdaptiveDifficultyEngine.adapt(session, tp, 0.6, strategy) # 0.6 is acceptable (between 0.5 and 0.8)
    assert tp.current_difficulty == DifficultyLevel.MEDIUM
    
def test_adapts_false_keeps_initial():
    session, tp, strategy = build_test_state(initial_diff=DifficultyLevel.MEDIUM, adapts=False)
    AdaptiveDifficultyEngine.adapt(session, tp, 0.9, strategy)
    assert tp.current_difficulty is None # It doesn't even set it if adapts is false and it wasn't set, fallback handles it
    
def test_campaign_band_clamps():
    # Strategy says Medium -> Strong -> Hard, but campaign says Max is Medium
    session, tp, strategy = build_test_state(initial_diff=DifficultyLevel.MEDIUM, band=[DifficultyLevel.EASY, DifficultyLevel.MEDIUM])
    AdaptiveDifficultyEngine.adapt(session, tp, 0.9, strategy)
    assert tp.current_difficulty == DifficultyLevel.MEDIUM
    
    # Strategy says Medium -> Weak -> Easy, but campaign says Min is Medium
    session, tp, strategy = build_test_state(initial_diff=DifficultyLevel.MEDIUM, band=[DifficultyLevel.MEDIUM, DifficultyLevel.HARD])
    AdaptiveDifficultyEngine.adapt(session, tp, 0.2, strategy)
    assert tp.current_difficulty == DifficultyLevel.MEDIUM

def test_resumes_own_difficulty():
    # If a topic already has current_difficulty, it adapts from that, not initial
    session, tp, strategy = build_test_state(initial_diff=DifficultyLevel.EASY, current_diff=DifficultyLevel.HARD)
    AdaptiveDifficultyEngine.adapt(session, tp, 0.2, strategy) # Weak -> moves to Medium
    assert tp.current_difficulty == DifficultyLevel.MEDIUM

def test_reset_on_switch_true():
    session, tp, strategy = build_test_state(initial_diff=DifficultyLevel.MEDIUM, current_diff=DifficultyLevel.HARD)
    strategy.difficulty_policy.reset_on_switch = True
    
    AdaptiveDifficultyEngine.handle_topic_switch(session, tp, previous_topic_id="t2", strategy=strategy)
    
    # Switched from t2 -> t1, reset_on_switch is True, so t1 resets to its initial (MEDIUM)
    assert tp.current_difficulty == DifficultyLevel.MEDIUM

def test_reset_on_switch_false():
    session, tp, strategy = build_test_state(initial_diff=DifficultyLevel.MEDIUM, current_diff=DifficultyLevel.HARD)
    strategy.difficulty_policy.reset_on_switch = False
    
    AdaptiveDifficultyEngine.handle_topic_switch(session, tp, previous_topic_id="t2", strategy=strategy)
    
    # Switched from t2 -> t1, reset_on_switch is False, so t1 preserves its current (HARD)
    assert tp.current_difficulty == DifficultyLevel.HARD
    
def test_continuing_same_topic_does_not_reset():
    session, tp, strategy = build_test_state(initial_diff=DifficultyLevel.MEDIUM, current_diff=DifficultyLevel.HARD)
    strategy.difficulty_policy.reset_on_switch = True
    
    # No switch occurred
    AdaptiveDifficultyEngine.handle_topic_switch(session, tp, previous_topic_id="t1", strategy=strategy)
    
    assert tp.current_difficulty == DifficultyLevel.HARD
    
def test_first_entry_initializes():
    session, tp, strategy = build_test_state(initial_diff=DifficultyLevel.HARD, current_diff=None)
    strategy.difficulty_policy.reset_on_switch = True
    
    # previous_topic_id is None because it's the first topic ever
    AdaptiveDifficultyEngine.handle_topic_switch(session, tp, previous_topic_id=None, strategy=strategy)
    
    assert tp.current_difficulty == DifficultyLevel.HARD

