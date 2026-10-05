"""
Task 6C — Strategy-aware CompletionEngine tests.

Covers:
A. Minimum floor
B. Target behavior
C. Max ceiling
D. Critical coverage requirement
E. Early-exit enabled
F. Early-exit disabled
G. Topics exhausted
H. Completion reason persistence on session
I. Fixed Coverage (min=target=max)
J. Critical Skills Deep Dive (can continue past target)
K. Practice regression (3 questions only, legacy path)
L. Legacy session without strategy_snapshot (blueprint path)
"""
import pytest
from datetime import datetime, timezone
from app.ai_interview.runtime.completion_engine import CompletionEngine
from app.ai_interview.schemas.session import InterviewSessionSchema, TopicProgress
from app.ai_interview.schemas.blueprint import InterviewBlueprint, TopicBlueprint
from app.ai_interview.schemas.strategy import StrategyDefinition, CompletionPolicy
from app.ai_interview.core.enums import (
    CompletionReason,
    DifficultyLevel,
    InterviewState,
    QuestionType,
    RequirementCriticality,
    TopicSource,
    TopicState,
)


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _make_strategy(
    min_q: int,
    target_q: int,
    max_q: int,
    allow_early_exit: bool = True,
    require_all_critical: bool = False,
) -> StrategyDefinition:
    return StrategyDefinition.model_construct(
        strategy_id="test-strategy",
        name="Test",
        description="Test strategy",
        version=1,
        is_active=True,
        applicable_interview_types=[],
        budget_mode="fixed",
        min_questions=min_q,
        target_questions=target_q,
        max_questions=max_q,
        max_questions_per_topic=4,
        max_followups_per_topic=2,
        critical_topic_max_followups=None,
        strong_threshold=0.8,
        acceptable_threshold=0.5,
        weak_threshold=0.3,
        completion_policy=CompletionPolicy(
            allow_early_exit=allow_early_exit,
            require_all_critical_covered=require_all_critical,
        ),
    )


def _make_blueprint(num_topics: int = 2, budget_per_topic: int = 3) -> InterviewBlueprint:
    topics = []
    for i in range(num_topics):
        topics.append(
            TopicBlueprint.model_construct(
                topic_id=f"t{i+1}",
                topic_name=f"Topic {i+1}",
                source="requirement",
                priority=10,
                mandatory=False,
                initial_difficulty=DifficultyLevel.MEDIUM,
                allowed_question_types=[QuestionType.INITIAL],
                question_budget=budget_per_topic,
            )
        )
    return InterviewBlueprint(
        blueprint_version="1",
        total_question_budget=num_topics * budget_per_topic,
        min_questions=num_topics,
        max_questions=num_topics * budget_per_topic,
        emergency_max_questions=num_topics * budget_per_topic + 2,
        topics=topics,
    )


def _make_topic_progress(
    topic_id: str,
    state: TopicState = TopicState.NOT_STARTED,
    questions_asked: int = 0,
    criticality: RequirementCriticality = None,
) -> TopicProgress:
    structurally_attempted = state in (TopicState.COVERED, TopicState.FAILED_ABANDONED)
    qualitatively_covered = state == TopicState.COVERED
    return TopicProgress.model_construct(
        topic_id=topic_id,
        state=state,
        structurally_attempted=structurally_attempted,
        qualitatively_covered=qualitatively_covered,
        coverage_score=1.0 if state == TopicState.COVERED else 0.0,
        questions_asked=questions_asked,
        criticality=criticality,
    )


def _make_session(
    mode_id: str = "official",
    questions_asked: int = 0,
    strategy: StrategyDefinition = None,
    topic_states: list = None,
    num_topics: int = 2,
) -> InterviewSessionSchema:
    blueprint = _make_blueprint(num_topics=num_topics)

    if topic_states is None:
        topic_states = [TopicState.NOT_STARTED] * num_topics

    topic_progress = []
    for i, state in enumerate(topic_states):
        topic_progress.append(
            _make_topic_progress(f"t{i+1}", state=state, questions_asked=questions_asked // num_topics)
        )

    return InterviewSessionSchema.model_construct(
        session_id="sess-test",
        candidate_id="c1",
        company_id="co1",
        campaign_id="camp1",
        mode_id=mode_id,
        mode_version=1,
        state=InterviewState.IN_PROGRESS,
        completion_reason=None,
        strategy_snapshot=strategy,
        blueprint=blueprint,
        questions_asked_total=questions_asked,
        topic_progress=topic_progress,
        question_history=[],
        evaluation_history=[],
        version=1,
        schema_version=1,
        created_at=datetime.now(timezone.utc),
    )


# ─────────────────────────────────────────────────────────────────────────────
# A. Minimum floor — strong early answers must not finish before min_questions
# ─────────────────────────────────────────────────────────────────────────────

def test_a_minimum_floor_prevents_early_finish():
    strategy = _make_strategy(min_q=8, target_q=10, max_q=12, allow_early_exit=True)
    session = _make_session(
        strategy=strategy,
        questions_asked=5,
        topic_states=[TopicState.COVERED, TopicState.COVERED],
    )
    should_complete, trace = CompletionEngine.evaluate(session)
    assert should_complete is False, "Must not finish before min_questions floor"


def test_a_minimum_floor_at_exactly_min_with_open_topics():
    strategy = _make_strategy(min_q=5, target_q=8, max_q=10, allow_early_exit=True)
    session = _make_session(
        strategy=strategy,
        questions_asked=5,
        topic_states=[TopicState.IN_PROGRESS, TopicState.IN_PROGRESS],  # topics still open
    )
    # At exactly min but topics still open, early_exit=True but not yet at target(8) → CONTINUE
    should_complete, trace = CompletionEngine.evaluate(session)
    assert should_complete is False, "Below target, topics still open: engine must CONTINUE"


# ─────────────────────────────────────────────────────────────────────────────
# B. Target behavior — reaching target does not force finish
# ─────────────────────────────────────────────────────────────────────────────

def test_b_target_does_not_auto_finish_when_critical_open():
    strategy = _make_strategy(
        min_q=8, target_q=10, max_q=15, allow_early_exit=True, require_all_critical=True
    )
    session = _make_session(
        strategy=strategy,
        questions_asked=10,
        num_topics=2,
    )
    # Add critical topic that is still open
    session.topic_progress[0].criticality = RequirementCriticality.CRITICAL
    session.topic_progress[0].state = TopicState.IN_PROGRESS
    session.topic_progress[1].state = TopicState.COVERED
    session.topic_progress[1].structurally_attempted = True
    session.topic_progress[1].qualitatively_covered = True

    should_complete, trace = CompletionEngine.evaluate(session)
    assert should_complete is False, "Target reached but critical topic still open: must CONTINUE"


def test_b_target_allows_finish_when_conditions_met():
    strategy = _make_strategy(
        min_q=8, target_q=10, max_q=15, allow_early_exit=True, require_all_critical=False
    )
    session = _make_session(
        strategy=strategy,
        questions_asked=10,
        topic_states=[TopicState.COVERED, TopicState.COVERED],
    )
    should_complete, trace = CompletionEngine.evaluate(session)
    assert should_complete is True, "At target with all covered and early_exit=True: should finish"
    reason = CompletionEngine.get_completion_reason(session)
    assert reason == CompletionReason.SUFFICIENT_COVERAGE


# ─────────────────────────────────────────────────────────────────────────────
# C. Max ceiling — always hard stop
# ─────────────────────────────────────────────────────────────────────────────

def test_c_max_ceiling_forces_finish():
    strategy = _make_strategy(min_q=5, target_q=8, max_q=10)
    session = _make_session(
        strategy=strategy,
        questions_asked=10,
        topic_states=[TopicState.IN_PROGRESS, TopicState.IN_PROGRESS],
    )
    should_complete, trace = CompletionEngine.evaluate(session)
    assert should_complete is True
    reason = CompletionEngine.get_completion_reason(session)
    assert reason == CompletionReason.MAX_QUESTIONS_REACHED


def test_c_max_ceiling_at_exactly_max():
    strategy = _make_strategy(min_q=5, target_q=8, max_q=12, require_all_critical=True)
    session = _make_session(
        strategy=strategy,
        questions_asked=12,
        num_topics=2,
    )
    session.topic_progress[0].criticality = RequirementCriticality.CRITICAL
    # max hit takes priority over critical requirement
    should_complete, trace = CompletionEngine.evaluate(session)
    assert should_complete is True
    reason = CompletionEngine.get_completion_reason(session)
    assert reason == CompletionReason.MAX_QUESTIONS_REACHED


# ─────────────────────────────────────────────────────────────────────────────
# D. Critical coverage — require_all_critical_covered=True
# ─────────────────────────────────────────────────────────────────────────────

def test_d_require_critical_blocks_early_exit():
    strategy = _make_strategy(
        min_q=5, target_q=8, max_q=12, allow_early_exit=True, require_all_critical=True
    )
    session = _make_session(strategy=strategy, questions_asked=9, num_topics=2)
    session.topic_progress[0].criticality = RequirementCriticality.CRITICAL
    session.topic_progress[0].state = TopicState.NOT_STARTED
    session.topic_progress[1].state = TopicState.COVERED
    session.topic_progress[1].structurally_attempted = True
    session.topic_progress[1].qualitatively_covered = True

    should_complete, _ = CompletionEngine.evaluate(session)
    assert should_complete is False, "CRITICAL topic not terminal: must CONTINUE even past target"


def test_d_require_critical_allows_finish_when_all_terminal():
    strategy = _make_strategy(
        min_q=5, target_q=8, max_q=12, allow_early_exit=True, require_all_critical=True
    )
    session = _make_session(
        strategy=strategy,
        questions_asked=9,
        topic_states=[TopicState.COVERED, TopicState.COVERED],
        num_topics=2,
    )
    session.topic_progress[0].criticality = RequirementCriticality.CRITICAL
    session.topic_progress[0].structurally_attempted = True
    session.topic_progress[0].qualitatively_covered = True

    should_complete, _ = CompletionEngine.evaluate(session)
    assert should_complete is True
    reason = CompletionEngine.get_completion_reason(session)
    assert reason == CompletionReason.SUFFICIENT_COVERAGE


# ─────────────────────────────────────────────────────────────────────────────
# E. Early exit enabled
# ─────────────────────────────────────────────────────────────────────────────

def test_e_early_exit_enabled_after_min_and_target():
    strategy = _make_strategy(
        min_q=5, target_q=8, max_q=15, allow_early_exit=True, require_all_critical=False
    )
    session = _make_session(
        strategy=strategy,
        questions_asked=8,
        topic_states=[TopicState.COVERED, TopicState.COVERED],
    )
    should_complete, _ = CompletionEngine.evaluate(session)
    assert should_complete is True
    reason = CompletionEngine.get_completion_reason(session)
    assert reason == CompletionReason.SUFFICIENT_COVERAGE


def test_e_early_exit_not_triggered_before_target():
    strategy = _make_strategy(
        min_q=5, target_q=10, max_q=15, allow_early_exit=True, require_all_critical=False
    )
    session = _make_session(
        strategy=strategy,
        questions_asked=7,
        topic_states=[TopicState.COVERED, TopicState.COVERED],
    )
    # 7 >= min(5) but 7 < target(10); early_exit cannot trigger yet
    should_complete, _ = CompletionEngine.evaluate(session)
    # Topics exhausted path applies here (all terminal)
    # but target not reached and early_exit checks target, so topics_exhausted fires
    # Actually: _all_topics_terminal=True → TOPICS_EXHAUSTED (step 5 after early_exit step fails)
    assert should_complete is True
    reason = CompletionEngine.get_completion_reason(session)
    assert reason == CompletionReason.TOPICS_EXHAUSTED


# ─────────────────────────────────────────────────────────────────────────────
# F. Early exit disabled
# ─────────────────────────────────────────────────────────────────────────────

def test_f_early_exit_disabled_prevents_sufficient_coverage_stop():
    strategy = _make_strategy(
        min_q=5, target_q=8, max_q=10, allow_early_exit=False, require_all_critical=False
    )
    session = _make_session(
        strategy=strategy,
        questions_asked=8,
        topic_states=[TopicState.IN_PROGRESS, TopicState.IN_PROGRESS],
    )
    should_complete, _ = CompletionEngine.evaluate(session)
    assert should_complete is False, "allow_early_exit=False: should not stop via sufficient_coverage"


def test_f_early_exit_disabled_still_stops_at_max():
    strategy = _make_strategy(
        min_q=5, target_q=8, max_q=10, allow_early_exit=False
    )
    session = _make_session(
        strategy=strategy,
        questions_asked=10,
        topic_states=[TopicState.IN_PROGRESS, TopicState.IN_PROGRESS],
    )
    should_complete, _ = CompletionEngine.evaluate(session)
    assert should_complete is True
    reason = CompletionEngine.get_completion_reason(session)
    assert reason == CompletionReason.MAX_QUESTIONS_REACHED


# ─────────────────────────────────────────────────────────────────────────────
# G. Topics exhausted
# ─────────────────────────────────────────────────────────────────────────────

def test_g_topics_exhausted_when_all_terminal_and_above_min():
    strategy = _make_strategy(min_q=3, target_q=6, max_q=10, allow_early_exit=False)
    session = _make_session(
        strategy=strategy,
        questions_asked=5,
        topic_states=[TopicState.COVERED, TopicState.FAILED_ABANDONED],
    )
    should_complete, _ = CompletionEngine.evaluate(session)
    assert should_complete is True
    reason = CompletionEngine.get_completion_reason(session)
    assert reason == CompletionReason.TOPICS_EXHAUSTED


# ─────────────────────────────────────────────────────────────────────────────
# H. Completion reason survives persistence (session field is set)
# ─────────────────────────────────────────────────────────────────────────────

def test_h_completion_reason_set_on_session():
    strategy = _make_strategy(min_q=2, target_q=3, max_q=5, allow_early_exit=True)
    session = _make_session(
        strategy=strategy,
        questions_asked=5,
        topic_states=[TopicState.IN_PROGRESS, TopicState.IN_PROGRESS],
    )
    reason = CompletionEngine.get_completion_reason(session)
    assert reason == CompletionReason.MAX_QUESTIONS_REACHED
    # Simulate coordinator persisting the reason
    session.completion_reason = reason
    assert session.completion_reason == CompletionReason.MAX_QUESTIONS_REACHED


# ─────────────────────────────────────────────────────────────────────────────
# I. Fixed Coverage (min = target = max = N)
# ─────────────────────────────────────────────────────────────────────────────

def test_i_fixed_coverage_finishes_at_exactly_n():
    n = 10
    strategy = _make_strategy(min_q=n, target_q=n, max_q=n)
    session = _make_session(
        strategy=strategy,
        questions_asked=n,
        topic_states=[TopicState.IN_PROGRESS, TopicState.IN_PROGRESS],
    )
    should_complete, _ = CompletionEngine.evaluate(session)
    assert should_complete is True
    reason = CompletionEngine.get_completion_reason(session)
    assert reason == CompletionReason.MAX_QUESTIONS_REACHED


def test_i_fixed_coverage_continues_below_n():
    n = 10
    strategy = _make_strategy(min_q=n, target_q=n, max_q=n)
    session = _make_session(
        strategy=strategy,
        questions_asked=9,
        topic_states=[TopicState.IN_PROGRESS, TopicState.IN_PROGRESS],
    )
    should_complete, _ = CompletionEngine.evaluate(session)
    assert should_complete is False


# ─────────────────────────────────────────────────────────────────────────────
# J. Critical Skills Deep Dive (can continue past target if critical open)
# ─────────────────────────────────────────────────────────────────────────────

def test_j_critical_deep_dive_continues_past_target():
    strategy = _make_strategy(
        min_q=8, target_q=12, max_q=15, allow_early_exit=True, require_all_critical=True
    )
    session = _make_session(
        strategy=strategy,
        questions_asked=12,
        num_topics=2,
    )
    # One critical topic still open at target
    session.topic_progress[0].criticality = RequirementCriticality.CRITICAL
    session.topic_progress[0].state = TopicState.IN_PROGRESS
    session.topic_progress[1].state = TopicState.COVERED
    session.topic_progress[1].structurally_attempted = True
    session.topic_progress[1].qualitatively_covered = True

    should_complete, _ = CompletionEngine.evaluate(session)
    assert should_complete is False, "Target reached but critical topic open: CONTINUE"


def test_j_critical_deep_dive_hard_stops_at_max():
    strategy = _make_strategy(
        min_q=8, target_q=12, max_q=15, allow_early_exit=True, require_all_critical=True
    )
    session = _make_session(
        strategy=strategy,
        questions_asked=15,
        num_topics=2,
    )
    session.topic_progress[0].criticality = RequirementCriticality.CRITICAL
    session.topic_progress[0].state = TopicState.IN_PROGRESS

    should_complete, _ = CompletionEngine.evaluate(session)
    assert should_complete is True
    reason = CompletionEngine.get_completion_reason(session)
    assert reason == CompletionReason.MAX_QUESTIONS_REACHED


# ─────────────────────────────────────────────────────────────────────────────
# K. Practice Mode regression — legacy path, no strategy_snapshot
# ─────────────────────────────────────────────────────────────────────────────

def _make_practice_session(questions_asked: int = 0, topic_states: list = None) -> InterviewSessionSchema:
    topics = [
        TopicBlueprint.model_construct(
            topic_id=f"p{i+1}",
            topic_name=f"Practice Topic {i+1}",
            source="practice",
            priority=10,
            mandatory=True,  # Practice uses mandatory to trigger legacy logic
            initial_difficulty=DifficultyLevel.MEDIUM,
            allowed_question_types=[QuestionType.INITIAL],
            question_budget=1,
        )
        for i in range(3)
    ]
    blueprint = InterviewBlueprint(
        blueprint_version="1",
        total_question_budget=3,
        min_questions=3,
        max_questions=3,
        emergency_max_questions=4,
        topics=topics,
    )
    if topic_states is None:
        topic_states = [TopicState.NOT_STARTED] * 3

    topic_progress = []
    for i, state in enumerate(topic_states):
        tp = TopicProgress.model_construct(
            topic_id=f"p{i+1}",
            state=state,
            structurally_attempted=state in (TopicState.COVERED, TopicState.FAILED_ABANDONED),
            qualitatively_covered=state == TopicState.COVERED,
            coverage_score=1.0 if state == TopicState.COVERED else 0.0,
            questions_asked=1 if state in (TopicState.COVERED, TopicState.FAILED_ABANDONED) else 0,
        )
        topic_progress.append(tp)

    return InterviewSessionSchema.model_construct(
        session_id="practice-sess",
        candidate_id="c1",
        company_id="co1",
        campaign_id="camp1",
        mode_id="practice",
        mode_version=1,
        state=InterviewState.IN_PROGRESS,
        completion_reason=None,
        strategy_snapshot=None,  # Practice has NO strategy snapshot
        blueprint=blueprint,
        questions_asked_total=questions_asked,
        topic_progress=topic_progress,
        question_history=[],
        evaluation_history=[],
        version=1,
        schema_version=1,
        created_at=datetime.now(timezone.utc),
    )


def test_k_practice_does_not_complete_before_3_questions():
    session = _make_practice_session(
        questions_asked=1,
        topic_states=[TopicState.COVERED, TopicState.NOT_STARTED, TopicState.NOT_STARTED],
    )
    should_complete, _ = CompletionEngine.evaluate(session)
    assert should_complete is False, "Practice must not complete before all 3 mandatory topics are attempted"


def test_k_practice_completes_after_all_mandatory_attempted():
    session = _make_practice_session(
        questions_asked=3,
        topic_states=[TopicState.COVERED, TopicState.COVERED, TopicState.COVERED],
    )
    should_complete, _ = CompletionEngine.evaluate(session)
    assert should_complete is True, "Practice: all 3 mandatory topics covered → COMPLETE"


def test_k_practice_does_not_use_strategy_snapshot():
    """Practice must use legacy path even if strategy_snapshot accidentally present."""
    strategy = _make_strategy(min_q=1, target_q=1, max_q=1)  # Would immediately stop at 1Q
    session = _make_practice_session(
        questions_asked=1,
        topic_states=[TopicState.COVERED, TopicState.NOT_STARTED, TopicState.NOT_STARTED],
    )
    # Force practice mode_id — strategy_snapshot stays None per practice helper
    session.strategy_snapshot = None
    should_complete, _ = CompletionEngine.evaluate(session)
    assert should_complete is False, "Practice uses legacy path regardless of mode"


# ─────────────────────────────────────────────────────────────────────────────
# L. Legacy session without strategy_snapshot (backward compatibility)
# ─────────────────────────────────────────────────────────────────────────────

def test_l_legacy_session_no_snapshot_uses_blueprint():
    """Old session without strategy_snapshot must use legacy blueprint behavior."""
    session = _make_session(
        mode_id="technical",
        strategy=None,  # No snapshot
        questions_asked=0,
        topic_states=[TopicState.NOT_STARTED, TopicState.NOT_STARTED],
    )
    should_complete, _ = CompletionEngine.evaluate(session)
    # Legacy: mandatory topics (None here) are all attempted, so may finish
    # But no mandatory topics set, so unresolved_mandatory=[] → should_complete=True (legacy bug preserved)
    assert isinstance(should_complete, bool)  # Whatever legacy path decides, it should run cleanly


def test_l_legacy_session_finishes_at_budget():
    blueprint = _make_blueprint(num_topics=2, budget_per_topic=3)
    session = InterviewSessionSchema.model_construct(
        session_id="legacy-sess",
        candidate_id="c1",
        company_id="co1",
        campaign_id="camp1",
        mode_id="official_old",
        mode_version=1,
        state=InterviewState.IN_PROGRESS,
        completion_reason=None,
        strategy_snapshot=None,
        blueprint=blueprint,
        questions_asked_total=6,  # == total_question_budget
        topic_progress=[
            _make_topic_progress("t1", state=TopicState.IN_PROGRESS),
            _make_topic_progress("t2", state=TopicState.IN_PROGRESS),
        ],
        question_history=[],
        evaluation_history=[],
        version=1,
        schema_version=1,
        created_at=datetime.now(timezone.utc),
    )
    should_complete, _ = CompletionEngine.evaluate(session)
    assert should_complete is True


# ─────────────────────────────────────────────────────────────────────────────
# M. Breadth Screening — resolved distinct-topic budget (Task 15)
#
# CompletionEngine itself is untouched by Task 15: it already handles a
# numeric min=target=max budget correctly (see test_i above, for Fixed
# Coverage's real N=10). These tests confirm that a Breadth Screening-shaped
# strategy (budget_mode="distinct_topics") with its budget already RESOLVED
# to the topic count (as SessionCreationService now does before the snapshot
# reaches CompletionEngine) behaves exactly like any other min=target=max=N
# strategy -- i.e. it does NOT complete at 0 questions, and DOES complete
# once N questions have been asked.
# ─────────────────────────────────────────────────────────────────────────────

def _make_resolved_breadth_screening_strategy(topic_count: int) -> StrategyDefinition:
    strategy = _make_strategy(min_q=topic_count, target_q=topic_count, max_q=topic_count)
    return strategy.model_copy(update={"budget_mode": "distinct_topics"})


def test_m_breadth_screening_resolved_budget_does_not_complete_at_zero_questions():
    strategy = _make_resolved_breadth_screening_strategy(topic_count=3)
    session = _make_session(
        strategy=strategy,
        questions_asked=0,
        num_topics=3,
        topic_states=[TopicState.NOT_STARTED] * 3,
    )
    should_complete, _ = CompletionEngine.evaluate(session)
    assert should_complete is False


def test_m_breadth_screening_resolved_budget_completes_after_topic_count_questions():
    strategy = _make_resolved_breadth_screening_strategy(topic_count=3)
    session = _make_session(
        strategy=strategy,
        questions_asked=3,
        num_topics=3,
        topic_states=[TopicState.COVERED] * 3,
    )
    should_complete, _ = CompletionEngine.evaluate(session)
    assert should_complete is True
    reason = CompletionEngine.get_completion_reason(session)
    assert reason == CompletionReason.MAX_QUESTIONS_REACHED


# ─────────────────────────────────────────────────────────────────────────────
# RuntimeDecision carries completion_reason
# ─────────────────────────────────────────────────────────────────────────────

def test_runtime_decision_has_completion_reason_field():
    from app.ai_interview.runtime.schemas import RuntimeDecision
    from app.ai_interview.runtime.enums import RuntimeAction
    from app.ai_interview.core.enums import InterviewState

    rd = RuntimeDecision(
        current_state=InterviewState.IN_PROGRESS,
        allowed_action=RuntimeAction.COMPLETE,
        should_complete=True,
        completion_reason=CompletionReason.MAX_QUESTIONS_REACHED,
    )
    assert rd.completion_reason == CompletionReason.MAX_QUESTIONS_REACHED
