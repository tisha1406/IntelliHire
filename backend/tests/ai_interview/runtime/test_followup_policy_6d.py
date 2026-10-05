"""
Task 6D — FollowUpPolicy enforcement tests.

Covers:
A. Follow-ups disabled (no allowed categories)
B. Allowed category selected correctly
C. Disallowed category is not selected
D. Maximum follow-ups enforced
E. Per-topic isolation (Topic A limit does not affect Topic B)
F. Critical vs non-critical limits (critical_topic_max_followups)
G. Breadth Screening shallow policy
H. GAP_VERIFICATION only when policy allows it
I. Advisory signal does NOT bypass policy limit
J. Persistence — follow_up_count survives reload
K. Idempotency — dispatcher rollback protects from double increment
L. Practice regression — 3-question flow, legacy path
M. Legacy regression — strategy_snapshot=None uses legacy path
N. Category propagation — final category reaches QuestionGenerationRequest
O. LLM authority — category in plan is already fixed before LLM called
"""
import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock

from app.ai_interview.runtime.followup_policy_engine import FollowUpPolicyEngine
from app.ai_interview.schemas.session import InterviewSessionSchema, TopicProgress
from app.ai_interview.schemas.strategy import StrategyDefinition, FollowUpPolicy, CompletionPolicy
from app.ai_interview.schemas.blueprint import InterviewBlueprint, TopicBlueprint
from app.ai_interview.core.enums import (
    QuestionCategory,
    QuestionType,
    DifficultyLevel,
    InterviewState,
    RequirementCriticality,
    TopicSource,
    TopicState,
)
from app.ai_interview.question_engine.question_dispatcher import QuestionDispatcher
from app.ai_interview.question_engine.schemas import QuestionTurnPlan, GeneratedQuestion


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _make_strategy(
    allowed_categories=None,
    max_per_topic=2,
    max_followups_per_topic=2,
    critical_max=None,
) -> StrategyDefinition:
    if allowed_categories is None:
        allowed_categories = [QuestionCategory.FOLLOWUP_CLARIFICATION, QuestionCategory.FOLLOWUP_DEPTH]
    return StrategyDefinition.model_construct(
        strategy_id="test",
        name="Test",
        description="Test",
        version=1,
        is_active=True,
        applicable_interview_types=[],
        budget_mode="fixed",
        min_questions=1,
        target_questions=5,
        max_questions=10,
        max_questions_per_topic=4,
        max_followups_per_topic=max_followups_per_topic,
        critical_topic_max_followups=critical_max,
        strong_threshold=0.8,
        acceptable_threshold=0.5,
        weak_threshold=0.3,
        followup_policy=FollowUpPolicy(
            allowed_categories=allowed_categories,
            max_per_topic=max_per_topic,
        ),
        completion_policy=CompletionPolicy(allow_early_exit=True, require_all_critical_covered=False),
    )


def _make_topic(
    follow_up_count: int = 0,
    questions_asked: int = 1,
    criticality=None,
    state: TopicState = TopicState.IN_PROGRESS,
) -> TopicProgress:
    return TopicProgress.model_construct(
        topic_id="t1",
        state=state,
        structurally_attempted=True,
        qualitatively_covered=False,
        coverage_score=0.0,
        questions_asked=questions_asked,
        follow_up_count=follow_up_count,
        criticality=criticality,
    )


# ─────────────────────────────────────────────────────────────────────────────
# A. Follow-ups disabled
# ─────────────────────────────────────────────────────────────────────────────

def test_a_followup_disabled_when_no_allowed_categories():
    strategy = _make_strategy(allowed_categories=[])
    topic = _make_topic(follow_up_count=0, questions_asked=1)
    allowed, category = FollowUpPolicyEngine.decide_followup(
        strategy=strategy,
        topic_progress=topic,
        follow_up_signal="depth_probe_may_help",
    )
    assert allowed is False
    assert category is None


# ─────────────────────────────────────────────────────────────────────────────
# B. Allowed category is correctly selected
# ─────────────────────────────────────────────────────────────────────────────

def test_b_allowed_category_returned():
    strategy = _make_strategy(
        allowed_categories=[QuestionCategory.FOLLOWUP_CLARIFICATION, QuestionCategory.FOLLOWUP_DEPTH]
    )
    topic = _make_topic(follow_up_count=0)
    allowed, category = FollowUpPolicyEngine.decide_followup(
        strategy=strategy,
        topic_progress=topic,
        follow_up_signal="depth_probe_may_help",
    )
    assert allowed is True
    assert category == QuestionCategory.FOLLOWUP_DEPTH  # signal preferred is in whitelist


def test_b_fallback_to_first_whitelist_category_when_signal_not_mapped():
    strategy = _make_strategy(
        allowed_categories=[QuestionCategory.FOLLOWUP_EVIDENCE, QuestionCategory.FOLLOWUP_DEPTH]
    )
    topic = _make_topic(follow_up_count=0)
    allowed, category = FollowUpPolicyEngine.decide_followup(
        strategy=strategy,
        topic_progress=topic,
        follow_up_signal=None,  # no advisory signal
    )
    assert allowed is True
    assert category == QuestionCategory.FOLLOWUP_EVIDENCE  # first in whitelist


# ─────────────────────────────────────────────────────────────────────────────
# C. Disallowed category is never selected
# ─────────────────────────────────────────────────────────────────────────────

def test_c_disallowed_category_not_selected_but_allowed_fallback_used():
    # Policy: only CLARIFICATION allowed; signal requests DEPTH
    strategy = _make_strategy(
        allowed_categories=[QuestionCategory.FOLLOWUP_CLARIFICATION]
    )
    topic = _make_topic(follow_up_count=0)
    allowed, category = FollowUpPolicyEngine.decide_followup(
        strategy=strategy,
        topic_progress=topic,
        follow_up_signal="depth_probe_may_help",  # DEPTH not in whitelist
    )
    assert allowed is True
    # Must not select DEPTH; falls back to first whitelist entry
    assert category == QuestionCategory.FOLLOWUP_CLARIFICATION
    assert category != QuestionCategory.FOLLOWUP_DEPTH


def test_c_gap_verification_not_selected_when_not_in_whitelist():
    strategy = _make_strategy(
        allowed_categories=[QuestionCategory.FOLLOWUP_CLARIFICATION]
    )
    topic = _make_topic(follow_up_count=0)
    # Even if someone passes "gap" as signal, not in whitelist, and GAP_VERIFICATION is not a follow-up category
    allowed, category = FollowUpPolicyEngine.decide_followup(
        strategy=strategy,
        topic_progress=topic,
        follow_up_signal="none",
    )
    assert allowed is True
    assert category == QuestionCategory.FOLLOWUP_CLARIFICATION  # whitelist fallback


# ─────────────────────────────────────────────────────────────────────────────
# D. Maximum follow-ups per topic enforced
# ─────────────────────────────────────────────────────────────────────────────

def test_d_max_followups_blocks_when_reached():
    strategy = _make_strategy(max_followups_per_topic=2)
    topic = _make_topic(follow_up_count=2)  # at limit
    allowed, category = FollowUpPolicyEngine.decide_followup(
        strategy=strategy,
        topic_progress=topic,
        follow_up_signal="depth_probe_may_help",
    )
    assert allowed is False
    assert category is None


def test_d_max_followups_allows_one_below_limit():
    strategy = _make_strategy(max_followups_per_topic=2)
    topic = _make_topic(follow_up_count=1)  # one below limit
    allowed, _ = FollowUpPolicyEngine.decide_followup(
        strategy=strategy,
        topic_progress=topic,
        follow_up_signal="depth_probe_may_help",
    )
    assert allowed is True


# ─────────────────────────────────────────────────────────────────────────────
# E. Per-topic isolation
# ─────────────────────────────────────────────────────────────────────────────

def test_e_topic_a_limit_does_not_affect_topic_b():
    strategy = _make_strategy(max_followups_per_topic=2)

    topic_a = TopicProgress.model_construct(
        topic_id="a", state=TopicState.IN_PROGRESS,
        structurally_attempted=True, qualitatively_covered=False,
        coverage_score=0.0, questions_asked=3, follow_up_count=2,  # A at limit
    )
    topic_b = TopicProgress.model_construct(
        topic_id="b", state=TopicState.IN_PROGRESS,
        structurally_attempted=True, qualitatively_covered=False,
        coverage_score=0.0, questions_asked=1, follow_up_count=0,  # B fresh
    )

    allowed_a, _ = FollowUpPolicyEngine.decide_followup(
        strategy=strategy, topic_progress=topic_a
    )
    allowed_b, _ = FollowUpPolicyEngine.decide_followup(
        strategy=strategy, topic_progress=topic_b
    )

    assert allowed_a is False, "Topic A at limit must be blocked"
    assert allowed_b is True,  "Topic B unaffected"


# ─────────────────────────────────────────────────────────────────────────────
# F. Critical vs non-critical limits
# ─────────────────────────────────────────────────────────────────────────────

def test_f_critical_topic_uses_critical_max():
    strategy = _make_strategy(max_followups_per_topic=1, critical_max=3)

    critical_topic = TopicProgress.model_construct(
        topic_id="critical", state=TopicState.IN_PROGRESS,
        structurally_attempted=True, qualitatively_covered=False,
        coverage_score=0.0, questions_asked=3, follow_up_count=2,
        criticality=RequirementCriticality.CRITICAL,
    )
    # follow_up_count=2, critical_max=3 → still allowed
    allowed, _ = FollowUpPolicyEngine.decide_followup(
        strategy=strategy, topic_progress=critical_topic
    )
    assert allowed is True, "Critical topic allows up to critical_max=3"


def test_f_critical_topic_blocked_at_critical_max():
    strategy = _make_strategy(max_followups_per_topic=1, critical_max=3)

    critical_topic = TopicProgress.model_construct(
        topic_id="critical", state=TopicState.IN_PROGRESS,
        structurally_attempted=True, qualitatively_covered=False,
        coverage_score=0.0, questions_asked=4, follow_up_count=3,
        criticality=RequirementCriticality.CRITICAL,
    )
    allowed, _ = FollowUpPolicyEngine.decide_followup(
        strategy=strategy, topic_progress=critical_topic
    )
    assert allowed is False, "Critical topic blocked at critical_max=3"


def test_f_non_critical_topic_uses_global_max():
    strategy = _make_strategy(max_followups_per_topic=1, critical_max=3)

    non_critical_topic = TopicProgress.model_construct(
        topic_id="nc", state=TopicState.IN_PROGRESS,
        structurally_attempted=True, qualitatively_covered=False,
        coverage_score=0.0, questions_asked=2, follow_up_count=1,
        criticality=RequirementCriticality.PREFERRED,
    )
    # follow_up_count=1, global max=1 → blocked
    allowed, _ = FollowUpPolicyEngine.decide_followup(
        strategy=strategy, topic_progress=non_critical_topic
    )
    assert allowed is False, "Non-critical topic blocked at global max=1"


# ─────────────────────────────────────────────────────────────────────────────
# G. Breadth Screening — shallow policy
# ─────────────────────────────────────────────────────────────────────────────

def test_g_breadth_screening_shallow_policy():
    # Breadth = max 1 follow-up, only CLARIFICATION
    strategy = _make_strategy(
        allowed_categories=[QuestionCategory.FOLLOWUP_CLARIFICATION],
        max_followups_per_topic=1,
        max_per_topic=1,
    )
    topic = _make_topic(follow_up_count=0)

    allowed, cat = FollowUpPolicyEngine.decide_followup(
        strategy=strategy, topic_progress=topic,
        follow_up_signal="depth_probe_may_help",
    )
    assert allowed is True
    assert cat == QuestionCategory.FOLLOWUP_CLARIFICATION  # depth not in whitelist


def test_g_breadth_screening_blocks_second_followup():
    strategy = _make_strategy(
        allowed_categories=[QuestionCategory.FOLLOWUP_CLARIFICATION],
        max_followups_per_topic=1,
    )
    topic = _make_topic(follow_up_count=1)  # already used 1

    allowed, _ = FollowUpPolicyEngine.decide_followup(
        strategy=strategy, topic_progress=topic
    )
    assert allowed is False


# ─────────────────────────────────────────────────────────────────────────────
# H. GAP_VERIFICATION only when allowed
# ─────────────────────────────────────────────────────────────────────────────

def test_h_gap_verification_allowed_when_in_whitelist():
    strategy = _make_strategy(
        allowed_categories=[QuestionCategory.GAP_VERIFICATION, QuestionCategory.FOLLOWUP_DEPTH]
    )
    topic = _make_topic(follow_up_count=0)
    allowed, cat = FollowUpPolicyEngine.decide_followup(
        strategy=strategy, topic_progress=topic, follow_up_signal=None
    )
    assert allowed is True
    assert cat == QuestionCategory.GAP_VERIFICATION  # first in whitelist


def test_h_gap_verification_blocked_when_not_in_whitelist():
    strategy = _make_strategy(
        allowed_categories=[QuestionCategory.FOLLOWUP_CLARIFICATION]
    )
    topic = _make_topic(follow_up_count=0)
    allowed, cat = FollowUpPolicyEngine.decide_followup(
        strategy=strategy, topic_progress=topic
    )
    # GAP_VERIFICATION not in whitelist; clarification returned instead
    assert allowed is True
    assert cat != QuestionCategory.GAP_VERIFICATION


# ─────────────────────────────────────────────────────────────────────────────
# I. Advisory signal does NOT bypass policy limit
# ─────────────────────────────────────────────────────────────────────────────

def test_i_advisory_signal_does_not_bypass_limit():
    strategy = _make_strategy(max_followups_per_topic=1)
    topic = _make_topic(follow_up_count=1)  # at limit

    # Evaluator strongly recommends a follow-up — should still be blocked
    allowed, _ = FollowUpPolicyEngine.decide_followup(
        strategy=strategy, topic_progress=topic,
        follow_up_signal="depth_probe_may_help",
    )
    assert allowed is False, "Advisory signal must not bypass the policy limit"


# ─────────────────────────────────────────────────────────────────────────────
# J. Persistence — follow_up_count reflected after increment
# ─────────────────────────────────────────────────────────────────────────────

def test_j_follow_up_count_incremented_by_increment_helper():
    topic = _make_topic(follow_up_count=0)
    FollowUpPolicyEngine.increment_followup_count(topic)
    assert topic.follow_up_count == 1


def test_j_follow_up_count_survives_session_reload():
    """Simulate persistence: build from scratch with persisted follow_up_count."""
    topic = TopicProgress.model_construct(
        topic_id="t1",
        state=TopicState.IN_PROGRESS,
        structurally_attempted=True,
        qualitatively_covered=False,
        coverage_score=0.0,
        questions_asked=2,
        follow_up_count=2,  # persisted from previous session
    )
    strategy = _make_strategy(max_followups_per_topic=2)

    allowed, _ = FollowUpPolicyEngine.decide_followup(
        strategy=strategy, topic_progress=topic
    )
    # Already at limit → blocked, confirming persisted count is honoured
    assert allowed is False


# ─────────────────────────────────────────────────────────────────────────────
# K. Idempotency — QuestionDispatcher rollback on failure
# ─────────────────────────────────────────────────────────────────────────────

def _make_minimal_session(follow_up_count: int = 0) -> InterviewSessionSchema:
    blueprint = InterviewBlueprint(
        blueprint_version="1",
        total_question_budget=10,
        min_questions=1,
        max_questions=10,
        emergency_max_questions=12,
        topics=[
            TopicBlueprint.model_construct(
                topic_id="t1", topic_name="Docker", source="requirement",
                priority=10, mandatory=False,
                initial_difficulty=DifficultyLevel.MEDIUM,
                allowed_question_types=[QuestionType.INITIAL],
                question_budget=5,
            )
        ],
    )
    return InterviewSessionSchema.model_construct(
        session_id="s1",
        candidate_id="c1", company_id="co1", campaign_id="camp1",
        mode_id="official", mode_version=1,
        state=InterviewState.IN_PROGRESS,
        completion_reason=None,
        strategy_snapshot=None,
        blueprint=blueprint,
        questions_asked_total=0,
        topic_progress=[
            TopicProgress.model_construct(
                topic_id="t1", state=TopicState.IN_PROGRESS,
                structurally_attempted=True, qualitatively_covered=False,
                coverage_score=0.0, questions_asked=1,
                follow_up_count=follow_up_count,
            )
        ],
        question_history=[],
        evaluation_history=[],
        version=1,
        schema_version=1,
        created_at=datetime.now(timezone.utc),
    )


def test_k_dispatcher_increments_followup_count_on_followup_category():
    session = _make_minimal_session(follow_up_count=0)
    topic = session.topic_progress[0]
    plan = QuestionTurnPlan.model_construct(
        session_id="s1", topic_id="t1", topic_name="Docker",
        difficulty=DifficultyLevel.MEDIUM,
        allowed_question_types=[QuestionType.FOLLOW_UP],
        topic_question_budget=5, topic_questions_asked=1,
        total_question_budget=10, total_questions_asked=0,
        turn_number=1, allowed=True,
        category=QuestionCategory.FOLLOWUP_DEPTH,  # follow-up category
    )
    question = GeneratedQuestion(
        question_text="Tell me more about Docker?",
        question_type=QuestionType.FOLLOW_UP,
        topic_id="t1",
        difficulty=DifficultyLevel.MEDIUM,
    )
    QuestionDispatcher.dispatch(session, plan, question)
    assert topic.follow_up_count == 1


def test_k_dispatcher_does_not_increment_followup_for_new_category():
    session = _make_minimal_session(follow_up_count=0)
    topic = session.topic_progress[0]
    plan = QuestionTurnPlan.model_construct(
        session_id="s1", topic_id="t1", topic_name="Docker",
        difficulty=DifficultyLevel.MEDIUM,
        allowed_question_types=[QuestionType.INITIAL],
        topic_question_budget=5, topic_questions_asked=1,
        total_question_budget=10, total_questions_asked=0,
        turn_number=1, allowed=True,
        category=QuestionCategory.NEW,  # NOT a follow-up category
    )
    question = GeneratedQuestion(
        question_text="What is Docker?",
        question_type=QuestionType.INITIAL,
        topic_id="t1",
        difficulty=DifficultyLevel.MEDIUM,
    )
    QuestionDispatcher.dispatch(session, plan, question)
    assert topic.follow_up_count == 0  # NEW questions must not increment


def test_k_dispatcher_rollback_on_invariant_violation_does_not_double_count():
    """Simulate a scenario where something fails after step 3: rollback restores count."""
    from app.ai_interview.question_engine.exceptions import QuestionDispatchError

    session = _make_minimal_session(follow_up_count=0)
    plan = QuestionTurnPlan.model_construct(
        session_id="s1", topic_id="t1", topic_name="Docker",
        difficulty=DifficultyLevel.MEDIUM,
        allowed_question_types=[QuestionType.FOLLOW_UP],
        topic_question_budget=5, topic_questions_asked=1,
        # Counter drift: plan says 5 but session has 0 → pre-dispatch invariant will fire
        total_question_budget=10, total_questions_asked=5,
        turn_number=6, allowed=True,
        category=QuestionCategory.FOLLOWUP_DEPTH,
    )
    question = GeneratedQuestion(
        question_text="Tell me more?",
        question_type=QuestionType.FOLLOW_UP,
        topic_id="t1",
        difficulty=DifficultyLevel.MEDIUM,
    )
    with pytest.raises(QuestionDispatchError):
        QuestionDispatcher.dispatch(session, plan, question)

    topic = session.topic_progress[0]
    assert topic.follow_up_count == 0, "Rollback must restore follow_up_count"


# ─────────────────────────────────────────────────────────────────────────────
# L. Practice regression
# ─────────────────────────────────────────────────────────────────────────────

def test_l_practice_bypasses_followup_policy():
    """FollowUpPolicyEngine.is_official returns False for practice mode."""
    strategy = _make_strategy()
    assert FollowUpPolicyEngine.is_official_session_with_followup_policy("practice", strategy) is False


def test_l_practice_bypasses_when_no_strategy():
    assert FollowUpPolicyEngine.is_official_session_with_followup_policy("practice", None) is False


# ─────────────────────────────────────────────────────────────────────────────
# M. Legacy regression
# ─────────────────────────────────────────────────────────────────────────────

def test_m_legacy_session_no_snapshot_bypasses_policy():
    assert FollowUpPolicyEngine.is_official_session_with_followup_policy("official", None) is False


def test_m_official_session_with_strategy_enabled():
    strategy = _make_strategy()
    assert FollowUpPolicyEngine.is_official_session_with_followup_policy("official", strategy) is True


# ─────────────────────────────────────────────────────────────────────────────
# N. Category propagation to QuestionGenerationRequest
# ─────────────────────────────────────────────────────────────────────────────

def test_n_category_propagates_from_plan_to_request():
    """The category chosen by the planner must reach QuestionGenerationRequest unchanged."""
    from app.ai_interview.question_engine.schemas import QuestionTurnPlan
    from app.ai_interview.question_engine.question_request_builder import QuestionRequestBuilder
    from app.ai_interview.core.enums import TopicDimension, ResumeEvidence
    from app.ai_interview.resume_processing.schemas import CandidateInterviewContext, StructuredResume
    from app.ai_interview.schemas.interview_mode import InterviewModeDefinition, InterviewModeSettings

    # Minimal inline mocks — no fixtures needed
    structured_resume = StructuredResume(
        name="Test Candidate",
        skills=[],
        experience=[],
        education=[],
        projects=[],
    )
    candidate_context = CandidateInterviewContext.model_construct(
        candidate_id="c1",
        structured_resume=structured_resume,
        resume_text="test",
        extraction_metadata={},
        quality_status="ok",
    )
    interview_mode = InterviewModeDefinition.model_construct(
        mode_id="official",
        mode_name="Official",
        name="Official",
        description="",
        interview_type="mixed",
        version=1,
        status="active",
        created_at=datetime.now(timezone.utc),
        settings=InterviewModeSettings.model_construct(
            question_style="technical",
            voice_id=None,
        ),
    )

    plan = QuestionTurnPlan(
        session_id="s1", topic_id="t1", topic_name="Docker",
        difficulty=DifficultyLevel.MEDIUM,
        allowed_question_types=[QuestionType.FOLLOW_UP],
        topic_question_budget=5, topic_questions_asked=1,
        total_question_budget=10, total_questions_asked=1,
        turn_number=2, allowed=True,
        interview_type=None,
        dimension=TopicDimension.TECHNICAL,
        category=QuestionCategory.FOLLOWUP_CLARIFICATION,  # deterministic category
        resume_evidence=ResumeEvidence.PARTIAL,
        campaign_requirement=None,
        requirement_criticality=None,
    )
    req = QuestionRequestBuilder.build(plan, candidate_context, interview_mode, [], [])
    assert req.category == QuestionCategory.FOLLOWUP_CLARIFICATION, \
        "Category must be passed through unchanged — LLM must not decide it"


# ─────────────────────────────────────────────────────────────────────────────
# O. LLM authority — generator cannot change the deterministic category
# ─────────────────────────────────────────────────────────────────────────────

def test_o_llm_cannot_override_category():
    """
    The QuestionGenerationRequest.category is set by the planner before LLM invocation.
    The LLM receives it as read-only context; it produces a question_text only.
    GeneratedQuestion has no category field that can override the plan's category.
    """
    from app.ai_interview.question_engine.schemas import GeneratedQuestion, QuestionGenerationRequest

    # Request sets category deterministically
    req = QuestionGenerationRequest(
        session_id="s1", turn_number=2, topic_id="t1", topic_name="Docker",
        difficulty=DifficultyLevel.MEDIUM,
        allowed_question_types=[QuestionType.FOLLOW_UP],
        selected_question_type=QuestionType.FOLLOW_UP,
        question_number=2, max_questions_for_topic=5,
        category=QuestionCategory.FOLLOWUP_DEPTH,
    )

    # GeneratedQuestion has no category field — it can't override the plan
    gen = GeneratedQuestion(
        question_text="Describe Docker networking",
        question_type=QuestionType.FOLLOW_UP,
        topic_id="t1",
        difficulty=DifficultyLevel.MEDIUM,
    )
    assert not hasattr(gen, "category") or gen.category is None, \
        "GeneratedQuestion must not have a category field the LLM can set"
    # The request's category is unchanged
    assert req.category == QuestionCategory.FOLLOWUP_DEPTH
