"""
Phase 4 — Deterministic Completion Engine

Strategy-aware completion for OFFICIAL interviews.

Design decisions:
  - For OFFICIAL sessions: session.strategy_snapshot is the authoritative source
    for min/target/max questions and completion_policy.
  - For sessions WITHOUT a strategy_snapshot (legacy or Practice): the legacy
    blueprint-based logic is preserved exactly.
  - Practice Mode is always served by the legacy path (mode_id == "practice").
  - The LLM has ZERO authority over completion.
  - completion_reason is returned alongside should_complete so the caller
    can persist it on session.completion_reason before saving.

Completion decision model (official):
  1. max_questions reached?          → FINISH  (max_questions_reached)
  2. below min_questions?            → CONTINUE
  3. require_all_critical_covered?   → if any critical topic non-terminal → CONTINUE
  4. allow_early_exit?               → if all required/critical terminal AND
                                        total >= target          → FINISH  (sufficient_coverage)
  5. no open topics remain?          → FINISH  (topics_exhausted)
  6. otherwise                       → CONTINUE
"""
from typing import Optional, Tuple
from app.ai_interview.schemas.session import InterviewSessionSchema, TopicProgress
from app.ai_interview.core.enums import (
    CompletionReason,
    DecisionReasonCode,
    InterviewDecision,
    RequirementCriticality,
    TopicState,
)
from app.ai_interview.schemas.decision_trace import CompletionDecisionTrace


# Criticality levels considered "critical" for require_all_critical_covered
_CRITICAL_CRITICALITIES = {RequirementCriticality.CRITICAL, RequirementCriticality.REQUIRED}


def _is_terminal(progress: TopicProgress) -> bool:
    return progress.state in (TopicState.COVERED, TopicState.FAILED_ABANDONED)


def _all_topics_terminal(session: InterviewSessionSchema) -> bool:
    return all(_is_terminal(p) for p in session.topic_progress)


def _critical_topics_all_terminal(session: InterviewSessionSchema) -> bool:
    """Return True if every topic with CRITICAL or REQUIRED criticality is terminal."""
    for p in session.topic_progress:
        if p.criticality in _CRITICAL_CRITICALITIES and not _is_terminal(p):
            return False
    return True


class CompletionEngine:
    """
    Deterministic completion evaluator.

    Returns (should_complete, completion_reason, trace).

    - should_complete: bool  — whether the runtime must stop the interview now.
    - completion_reason: Optional[CompletionReason]  — populated when should_complete=True.
    - trace: CompletionDecisionTrace  — observability only; never drives LLM decisions.
    """

    @staticmethod
    def evaluate(
        session: InterviewSessionSchema,
    ) -> Tuple[bool, CompletionDecisionTrace]:
        """
        Backward-compatible public interface used by RuntimeController.

        Returns (should_complete, trace).
        The completion_reason is embedded in trace.reason_codes as the FIRST entry
        when should_complete=True.  RuntimeController must call get_completion_reason()
        to retrieve the typed CompletionReason when it needs to persist it.
        """
        should_complete, reason, trace = CompletionEngine._evaluate_full(session)
        return should_complete, trace

    @staticmethod
    def get_completion_reason(session: InterviewSessionSchema) -> Optional[CompletionReason]:
        """
        Return the CompletionReason for a session that evaluate() already decided
        should complete.  Call this before persisting the session.
        """
        should_complete, reason, _ = CompletionEngine._evaluate_full(session)
        if should_complete:
            return reason
        return None

    # ─────────────────────────────────────────────────────────────────────────
    # Internal implementation
    # ─────────────────────────────────────────────────────────────────────────

    @staticmethod
    def _evaluate_full(
        session: InterviewSessionSchema,
    ) -> Tuple[bool, Optional[CompletionReason], CompletionDecisionTrace]:
        """
        Core evaluation.  Returns (should_complete, completion_reason, trace).
        """
        is_practice = getattr(session, "mode_id", None) == "practice"
        has_strategy = (
            not is_practice
            and session.strategy_snapshot is not None
        )

        if has_strategy:
            return CompletionEngine._evaluate_official(session)
        else:
            return CompletionEngine._evaluate_legacy(session)

    # ── Official strategy-aware path ─────────────────────────────────────────

    @staticmethod
    def _evaluate_official(
        session: InterviewSessionSchema,
    ) -> Tuple[bool, Optional[CompletionReason], CompletionDecisionTrace]:
        strategy = session.strategy_snapshot  # StrategyDefinition (immutable snapshot)
        bp = session.blueprint
        asked = session.questions_asked_total

        min_q = strategy.min_questions
        target_q = strategy.target_questions
        max_q = strategy.max_questions
        allow_early = strategy.completion_policy.allow_early_exit
        require_critical = strategy.completion_policy.require_all_critical_covered

        reason_codes: list[DecisionReasonCode] = []

        # ── 1. Hard ceiling ───────────────────────────────────────────────────
        if asked >= max_q:
            reason_codes.append(DecisionReasonCode.QUESTION_BUDGET_REACHED)
            return (
                True,
                CompletionReason.MAX_QUESTIONS_REACHED,
                CompletionEngine._make_trace(
                    session, min_q, max_q, True, reason_codes,
                    InterviewDecision.COMPLETE,
                ),
            )

        # ── 2. Minimum floor — never finish below this ────────────────────────
        if asked < min_q:
            reason_codes.append(DecisionReasonCode.MINIMUM_QUESTIONS_NOT_MET)
            return (
                False,
                None,
                CompletionEngine._make_trace(
                    session, min_q, max_q, False, reason_codes,
                    InterviewDecision.NEXT_TOPIC,
                ),
            )

        # ── 3. Critical coverage requirement ─────────────────────────────────
        if require_critical and not _critical_topics_all_terminal(session):
            reason_codes.append(DecisionReasonCode.MANDATORY_TOPICS_PENDING)
            return (
                False,
                None,
                CompletionEngine._make_trace(
                    session, min_q, max_q, False, reason_codes,
                    InterviewDecision.NEXT_TOPIC,
                ),
            )

        # ── 4. Early-exit — allowed only after min; subject to critical check ─
        if allow_early:
            critical_done = _critical_topics_all_terminal(session)
            if critical_done and asked >= target_q:
                reason_codes.append(DecisionReasonCode.CONFIDENCE_THRESHOLD_MET)
                reason_codes.append(DecisionReasonCode.MANDATORY_TOPICS_ATTEMPTED)
                return (
                    True,
                    CompletionReason.SUFFICIENT_COVERAGE,
                    CompletionEngine._make_trace(
                        session, min_q, max_q, True, reason_codes,
                        InterviewDecision.COMPLETE,
                    ),
                )

        # ── 5. No open topics remain ──────────────────────────────────────────
        if _all_topics_terminal(session):
            reason_codes.append(DecisionReasonCode.MANDATORY_TOPICS_ATTEMPTED)
            return (
                True,
                CompletionReason.TOPICS_EXHAUSTED,
                CompletionEngine._make_trace(
                    session, min_q, max_q, True, reason_codes,
                    InterviewDecision.COMPLETE,
                ),
            )

        # ── 6. Continue ───────────────────────────────────────────────────────
        return (
            False,
            None,
            CompletionEngine._make_trace(
                session, min_q, max_q, False, [],
                InterviewDecision.NEXT_TOPIC,
            ),
        )

    # ── Legacy blueprint path (Practice + old sessions without snapshot) ─────

    @staticmethod
    def _evaluate_legacy(
        session: InterviewSessionSchema,
    ) -> Tuple[bool, Optional[CompletionReason], CompletionDecisionTrace]:
        """
        Preserves the ORIGINAL completion behavior for Practice Mode and for any
        session that was created before strategy_snapshot was introduced.

        Original logic:
        - Finish when all mandatory topics are terminal (covered/abandoned).
        - Finish when total_question_budget is exhausted.
        """
        bp = session.blueprint

        mandatory_topic_ids = {t.topic_id for t in bp.topics if t.mandatory}

        unresolved_mandatory = []
        abandoned_mandatory = []
        covered_mandatory = []

        for prog in session.topic_progress:
            if prog.topic_id in mandatory_topic_ids:
                if prog.state == TopicState.COVERED:
                    covered_mandatory.append(prog)
                elif prog.state == TopicState.FAILED_ABANDONED:
                    abandoned_mandatory.append(prog)
                else:
                    unresolved_mandatory.append(prog)

        mandatory_attempted = len(unresolved_mandatory) == 0

        reason_codes: list[DecisionReasonCode] = []
        should_complete = False
        completion_reason: Optional[CompletionReason] = None

        if len(unresolved_mandatory) > 0:
            reason_codes.append(DecisionReasonCode.MANDATORY_TOPICS_PENDING)
        else:
            reason_codes.append(DecisionReasonCode.MANDATORY_TOPICS_ATTEMPTED)
            should_complete = True
            completion_reason = CompletionReason.MANDATORY_TOPICS_ATTEMPTED
            if len(abandoned_mandatory) == 0:
                reason_codes.append(DecisionReasonCode.CONFIDENCE_THRESHOLD_MET)
            else:
                reason_codes.append(DecisionReasonCode.LOW_TOPIC_COVERAGE)

        # Budget check — overrides if exhausted
        if session.questions_asked_total >= bp.total_question_budget:
            should_complete = True
            completion_reason = CompletionReason.MAX_QUESTIONS_REACHED
            reason_codes.append(DecisionReasonCode.QUESTION_BUDGET_REACHED)

        trace = CompletionDecisionTrace(
            questions_asked_total=session.questions_asked_total,
            min_questions=bp.min_questions,
            max_questions=bp.max_questions,
            emergency_max_questions=bp.emergency_max_questions,
            mandatory_topics_attempted=mandatory_attempted,
            overall_confidence=0.0,
            threshold=0.0,
            decision=InterviewDecision.COMPLETE if should_complete else InterviewDecision.NEXT_TOPIC,
            reason_codes=reason_codes,
        )

        return should_complete, completion_reason, trace

    # ── Trace builder ────────────────────────────────────────────────────────

    @staticmethod
    def _make_trace(
        session: InterviewSessionSchema,
        min_q: int,
        max_q: int,
        should_complete: bool,
        reason_codes: list,
        decision: InterviewDecision,
    ) -> CompletionDecisionTrace:
        bp = session.blueprint
        return CompletionDecisionTrace(
            questions_asked_total=session.questions_asked_total,
            min_questions=min_q,
            max_questions=max_q,
            emergency_max_questions=bp.emergency_max_questions,
            mandatory_topics_attempted=_critical_topics_all_terminal(session),
            overall_confidence=0.0,
            threshold=0.0,
            decision=decision,
            reason_codes=reason_codes,
        )
