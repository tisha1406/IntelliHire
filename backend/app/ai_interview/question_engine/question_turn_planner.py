"""
Phase 5 — Question Orchestration & Interview Turn Engine

QuestionTurnPlanner: Deterministic component that decides whether a question
may be legally asked given current session state, runtime decision, and budgets.

Authority:
  - Consumes RuntimeDecision from Phase 4 RuntimeController.
  - Does NOT independently select topics; topic selection is Phase 4's domain.
  - Checks global and per-topic budgets BEFORE any generation is attempted.
  - Returns QuestionTurnPlan with allowed=False when any check fails.
"""
from typing import Optional

from app.ai_interview.core.enums import InterviewState, QuestionType
from app.ai_interview.runtime.enums import RuntimeAction
from app.ai_interview.runtime.schemas import RuntimeDecision
from app.ai_interview.schemas.blueprint import InterviewBlueprint, TopicBlueprint
from app.ai_interview.schemas.session import InterviewSessionSchema, TopicProgress
from app.ai_interview.question_engine.enums import TurnDenialReason
from app.ai_interview.question_engine.schemas import QuestionTurnPlan


class QuestionTurnPlanner:
    """
    Deterministic permission engine for a single question turn.

    Same input → same QuestionTurnPlan.  No side effects.  No mutations.
    """

    @staticmethod
    def plan(
        session: InterviewSessionSchema,
        runtime_decision: RuntimeDecision,
    ) -> QuestionTurnPlan:
        """
        Evaluate whether the engine may ask a question right now.

        Returns a QuestionTurnPlan with allowed=True when all checks pass,
        or allowed=False with a denial_reason when any check fails.
        The caller (QuestionEngine) must abort generation when allowed=False.
        """
        blueprint: InterviewBlueprint = session.blueprint

        # ── 1. Session must be IN_PROGRESS ──────────────────────────────────
        if session.state != InterviewState.IN_PROGRESS:
            return QuestionTurnPlanner._deny(
                session_id=session.session_id,
                blueprint=blueprint,
                session=session,
                runtime_decision=runtime_decision,
                reason=TurnDenialReason.INTERVIEW_NOT_IN_PROGRESS,
            )

        # ── 2. Runtime decision must carry an active topic ───────────────────
        # RuntimeAction.COMPLETE and RuntimeAction.NO_ACTION (without active topic)
        # mean the deterministic runtime is not authorising a new question.
        if runtime_decision.active_topic_id is None or runtime_decision.should_complete:
            return QuestionTurnPlanner._deny(
                session_id=session.session_id,
                blueprint=blueprint,
                session=session,
                runtime_decision=runtime_decision,
                reason=TurnDenialReason.RUNTIME_DOES_NOT_AUTHORIZE,
            )

        topic_id: str = runtime_decision.active_topic_id

        # ── 3. Resolve topic blueprint ───────────────────────────────────────
        topic_bp: Optional[TopicBlueprint] = next(
            (t for t in blueprint.topics if t.topic_id == topic_id), None
        )
        if topic_bp is None:
            return QuestionTurnPlanner._deny(
                session_id=session.session_id,
                blueprint=blueprint,
                session=session,
                runtime_decision=runtime_decision,
                reason=TurnDenialReason.TOPIC_NOT_FOUND_IN_BLUEPRINT,
            )

        # ── 4. Resolve topic progress ────────────────────────────────────────
        topic_progress: Optional[TopicProgress] = next(
            (p for p in session.topic_progress if p.topic_id == topic_id), None
        )
        # topic_progress must exist (SessionInitializer guarantees it), but be safe:
        if topic_progress is None:
            return QuestionTurnPlanner._deny(
                session_id=session.session_id,
                blueprint=blueprint,
                session=session,
                runtime_decision=runtime_decision,
                reason=TurnDenialReason.NO_ACTIVE_TOPIC,
            )

        # ── 5. Global question budget ────────────────────────────────────────
        if session.questions_asked_total >= blueprint.total_question_budget:
            return QuestionTurnPlanner._deny(
                session_id=session.session_id,
                blueprint=blueprint,
                session=session,
                runtime_decision=runtime_decision,
                reason=TurnDenialReason.GLOBAL_BUDGET_EXHAUSTED,
            )

        # ── 6. Per-topic question budget ─────────────────────────────────────
        if topic_progress.questions_asked >= topic_bp.question_budget:
            return QuestionTurnPlanner._deny(
                session_id=session.session_id,
                blueprint=blueprint,
                session=session,
                runtime_decision=runtime_decision,
                reason=TurnDenialReason.TOPIC_BUDGET_EXHAUSTED,
            )

        # ── 7. All checks passed — build the plan ────────────────────────────
        turn_number: int = session.questions_asked_total + 1

        allowed_types: list[QuestionType] = list(topic_bp.allowed_question_types)
        if not allowed_types:
            # Fallback to INITIAL when no types are configured (rare but safe)
            allowed_types = [QuestionType.INITIAL]
            
        # The category is decided here — the LLM NEVER overrides this decision.
        from app.ai_interview.core.enums import QuestionCategory, TopicSource
        from app.ai_interview.runtime.followup_policy_engine import FollowUpPolicyEngine

        if topic_progress.questions_asked == 0:
            # First question on topic
            if topic_progress.source == TopicSource.GAP and QuestionTurnPlanner._gap_verification_allowed(session):
                category = QuestionCategory.GAP_VERIFICATION
            else:
                # Either not a gap topic, or a gap topic under a strategy
                # whose registry combination does not allow
                # gap_verification (FC/CS/BS/BA): NEW is allowed by every
                # combination and keeps the strategy's own blocks/addendum.
                category = QuestionCategory.NEW
        else:
            # Not the first question — decide whether a policy-permitted follow-up
            # is allowed, or fall back to NEW.
            is_official = FollowUpPolicyEngine.is_official_session_with_followup_policy(
                mode_id=session.mode_id,
                strategy=session.strategy_snapshot,
            )
            if is_official:
                # Read the advisory evaluator signal from the last evaluation
                follow_up_signal = None
                if session.evaluation_history:
                    last_eval = session.evaluation_history[-1]
                    # Only use signal if it concerns the current topic
                    if last_eval.topic_id == topic_id:
                        fu_sig = last_eval.follow_up_signal
                        follow_up_signal = fu_sig.value if hasattr(fu_sig, "value") else str(fu_sig)

                allowed, fu_category = FollowUpPolicyEngine.decide_followup(
                    strategy=session.strategy_snapshot,
                    topic_progress=topic_progress,
                    follow_up_signal=follow_up_signal,
                )
                if allowed and fu_category is not None:
                    category = fu_category
                else:
                    # Follow-up not permitted by policy → NEW question on same topic
                    category = QuestionCategory.NEW
            else:
                # Legacy / Practice path: use FOLLOWUP_DEPTH as before
                category = QuestionCategory.FOLLOWUP_DEPTH

        current_difficulty = topic_progress.current_difficulty or topic_bp.initial_difficulty

        # Get strategy info if available
        strategy = None
        strategy_id = None
        if session.strategy_snapshot:
            strategy = session.strategy_snapshot.name
            strategy_id = session.strategy_snapshot.strategy_id

        return QuestionTurnPlan(
            session_id=session.session_id,
            topic_id=topic_id,
            topic_name=topic_bp.topic_name,
            difficulty=current_difficulty,
            allowed_question_types=allowed_types,
            topic_question_budget=topic_bp.question_budget,
            topic_questions_asked=topic_progress.questions_asked,
            total_question_budget=blueprint.total_question_budget,
            total_questions_asked=session.questions_asked_total,
            turn_number=turn_number,
            allowed=True,
            denial_reason=None,
            
            interview_type=session.interview_type,
            strategy=strategy,
            strategy_id=strategy_id,
            dimension=topic_progress.dimension,
            category=category,
            resume_evidence=topic_progress.resume_evidence,
            candidate_claim=topic_progress.candidate_claim,
            interview_evidence=topic_progress.interview_evidence,
            campaign_requirement=topic_progress.campaign_requirement,
            requirement_criticality=topic_progress.criticality,
            # D-04: topic_bp is the same TopicBlueprint instance already
            # supplying topic_name/difficulty/question_budget above. It
            # carries the D-03 snapshot (scenario_id/scenario_context),
            # None for every non-situational topic, so this needs no extra
            # conditional -- a Technical/Resume/Behavioral/GAP topic's
            # topic_bp.scenario_context is already None by construction
            # (CoveragePlanner only ever sets it for a SITUATIONAL_SCENARIO-
            # sourced topic). No new lookup, no new field.
            scenario_context=topic_bp.scenario_context,
            specificity_required=topic_progress.current_specificity if hasattr(topic_progress, "current_specificity") else None,
        )

    # ── Private helpers ──────────────────────────────────────────────────────

    @staticmethod
    def _gap_verification_allowed(session: InterviewSessionSchema) -> bool:
        """True unless this session's strategy/interview-type combination is
        known to the prompt registry AND its allowed categories exclude
        gap_verification.

        Sessions without a strategy snapshot or interview type (Practice,
        legacy) never go through PromptResolver's registry validation, and an
        unrecognised combination is left for PromptResolver to report, so
        both keep the existing GAP_VERIFICATION behaviour.
        """
        if session.strategy_snapshot is None or session.interview_type is None:
            return True
        from app.ai_interview.question_engine.prompts.registry import get_combination
        combo = get_combination(session.strategy_snapshot.strategy_id, session.interview_type.value)
        if combo is None:
            return True
        return "gap_verification" in combo.allowed_categories

    @staticmethod
    def _deny(
        session_id: str,
        blueprint: InterviewBlueprint,
        session: InterviewSessionSchema,
        runtime_decision: RuntimeDecision,
        reason: TurnDenialReason,
    ) -> QuestionTurnPlan:
        """Build a denied QuestionTurnPlan with safe placeholder values."""
        topic_id = runtime_decision.active_topic_id or ""
        topic_bp = next((t for t in blueprint.topics if t.topic_id == topic_id), None)
        topic_progress = next(
            (p for p in session.topic_progress if p.topic_id == topic_id), None
        )

        from app.ai_interview.core.enums import DifficultyLevel

        return QuestionTurnPlan(
            session_id=session_id,
            topic_id=topic_id,
            topic_name=topic_bp.topic_name if topic_bp else "",
            difficulty=topic_bp.initial_difficulty if topic_bp else DifficultyLevel.MEDIUM,
            allowed_question_types=list(topic_bp.allowed_question_types) if topic_bp else [],
            topic_question_budget=topic_bp.question_budget if topic_bp else 0,
            topic_questions_asked=topic_progress.questions_asked if topic_progress else 0,
            total_question_budget=blueprint.total_question_budget,
            total_questions_asked=session.questions_asked_total,
            turn_number=session.questions_asked_total + 1,
            allowed=False,
            denial_reason=reason,
            interview_type=session.interview_type,
            strategy=session.strategy_snapshot.name if session.strategy_snapshot else None,
            strategy_id=session.strategy_snapshot.strategy_id if session.strategy_snapshot else None,
            dimension=topic_progress.dimension if topic_progress else None,
            category=None,
            resume_evidence=topic_progress.resume_evidence if topic_progress else None,
            candidate_claim=topic_progress.candidate_claim if topic_progress else None,
            interview_evidence=topic_progress.interview_evidence if topic_progress else None,
            campaign_requirement=topic_progress.campaign_requirement if topic_progress else None,
            requirement_criticality=topic_progress.criticality if topic_progress else None,
            # D-04: same topic_bp-sourced snapshot as the allowed-plan path
            # above; a denied plan still carries the blueprint's real value
            # when topic_bp was resolved (it may be None if the topic wasn't
            # found at all, same fallback already used for every other
            # topic_bp-derived field in this denial plan).
            scenario_context=topic_bp.scenario_context if topic_bp else None,
            specificity_required=topic_progress.current_specificity if topic_progress and hasattr(topic_progress, "current_specificity") else None,
        )
