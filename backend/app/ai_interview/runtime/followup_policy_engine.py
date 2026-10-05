"""
FollowUpPolicyEngine — Deterministic follow-up policy enforcer.

This module is the single authoritative place for evaluating whether a follow-up
question is permitted according to the strategy's FollowUpPolicy.

Design principles:
  - The LLM / evaluator may indicate a follow-up is recommended (advisory).
  - This engine independently decides whether one is ALLOWED.
  - Allowed = (strategy permits follow-ups) AND (allowed category exists)
              AND (per-topic limit not reached).
  - Critical vs non-critical limit is resolved via
    StrategyDefinition.critical_topic_max_followups (non-None → use for critical).
  - Practice Mode and legacy sessions (no strategy_snapshot) bypass this engine.
"""
from typing import Optional, Tuple

from app.ai_interview.core.enums import QuestionCategory, RequirementCriticality
from app.ai_interview.schemas.session import TopicProgress
from app.ai_interview.schemas.strategy import StrategyDefinition

# The mapping of FollowUpSignal advisory values → preferred QuestionCategory.
# Only used when no explicit preferred_category is passed.
_SIGNAL_TO_CATEGORY = {
    "clarification_may_help": QuestionCategory.FOLLOWUP_CLARIFICATION,
    "depth_probe_may_help": QuestionCategory.FOLLOWUP_DEPTH,
}

# Criticality values that are treated as "critical" for follow-up limit lookup
_CRITICAL_CRITICALITIES = {RequirementCriticality.CRITICAL, RequirementCriticality.REQUIRED}


class FollowUpPolicyEngine:
    """
    Deterministic follow-up gating and category selection.

    Usage:
        allowed, category = FollowUpPolicyEngine.decide_followup(
            strategy=session.strategy_snapshot,
            topic_progress=active_topic,
            follow_up_signal="depth_probe_may_help",   # advisory only
        )
        if allowed:
            # use `category` as the deterministic QuestionCategory
        else:
            # select NEW question or move to next topic per priority engine
    """

    @staticmethod
    def decide_followup(
        strategy: StrategyDefinition,
        topic_progress: TopicProgress,
        follow_up_signal: Optional[str] = None,  # value of FollowUpSignal enum (advisory only)
    ) -> Tuple[bool, Optional[QuestionCategory]]:
        """
        Determine whether a follow-up question is permitted and which category to use.

        Args:
            strategy:         Immutable StrategyDefinition from session.strategy_snapshot.
            topic_progress:   Current topic's progress state (contains follow_up_count).
            follow_up_signal: Advisory signal from the evaluator (FollowUpSignal.value string).
                              This is ADVISORY ONLY — it does not override policy limits.

        Returns:
            (True, selected_category)  if a follow-up is allowed.
            (False, None)              if a follow-up is not allowed.
        """
        policy = strategy.followup_policy

        # ── 1. Is ANY follow-up category allowed at all? ─────────────────────
        if not policy.allowed_categories:
            return False, None

        # ── 2. Per-topic follow-up limit (critical vs non-critical) ──────────
        max_followups = FollowUpPolicyEngine._resolve_max_followups(strategy, topic_progress)
        if topic_progress.follow_up_count >= max_followups:
            return False, None

        # ── 3. Select the best allowed category ──────────────────────────────
        selected_category = FollowUpPolicyEngine._select_category(
            allowed_categories=policy.allowed_categories,
            follow_up_signal=follow_up_signal,
        )
        if selected_category is None:
            return False, None

        return True, selected_category

    # ── Private helpers ───────────────────────────────────────────────────────

    @staticmethod
    def _resolve_max_followups(
        strategy: StrategyDefinition,
        topic_progress: TopicProgress,
    ) -> int:
        """
        Return the applicable follow-up limit for this topic.

        Critical Skills Deep Dive stores critical_topic_max_followups separately.
        When that field is set AND the topic is CRITICAL/REQUIRED, use it.
        Otherwise fall back to max_followups_per_topic.
        """
        is_critical = topic_progress.criticality in _CRITICAL_CRITICALITIES

        if is_critical and strategy.critical_topic_max_followups is not None:
            return strategy.critical_topic_max_followups

        return strategy.max_followups_per_topic

    @staticmethod
    def _select_category(
        allowed_categories: list,
        follow_up_signal: Optional[str],
    ) -> Optional[QuestionCategory]:
        """
        Choose the best allowed QuestionCategory.

        Priority:
          1. Preferred category mapped from the advisory follow_up_signal,
             if it is in the allowed_categories whitelist.
          2. First entry in the whitelist (deterministic fallback).
          3. None if the whitelist is empty (caller interprets as no follow-up).
        """
        if not allowed_categories:
            return None

        # Try to honor the advisory signal's preferred category
        if follow_up_signal and follow_up_signal in _SIGNAL_TO_CATEGORY:
            preferred = _SIGNAL_TO_CATEGORY[follow_up_signal]
            if preferred in allowed_categories:
                return preferred

        # Fallback: first entry in the whitelist (deterministic)
        return allowed_categories[0]

    @staticmethod
    def increment_followup_count(topic_progress: TopicProgress) -> None:
        """
        Increment the authoritative follow-up counter on the topic.

        MUST be called only after a follow-up question has been successfully
        dispatched (persisted). Must NOT be called on generation failure,
        retry, or duplicate evaluation.
        """
        topic_progress.follow_up_count += 1

    @staticmethod
    def is_official_session_with_followup_policy(
        mode_id: str,
        strategy: Optional[StrategyDefinition],
    ) -> bool:
        """
        Return True if this session should have FollowUpPolicy enforced.

        Practice Mode and legacy sessions without a strategy_snapshot skip enforcement.
        """
        if mode_id == "practice":
            return False
        if strategy is None:
            return False
        return True
