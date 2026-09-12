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

        return QuestionTurnPlan(
            session_id=session.session_id,
            topic_id=topic_id,
            topic_name=topic_bp.topic_name,
            difficulty=topic_bp.initial_difficulty,
            allowed_question_types=allowed_types,
            topic_question_budget=topic_bp.question_budget,
            topic_questions_asked=topic_progress.questions_asked,
            total_question_budget=blueprint.total_question_budget,
            total_questions_asked=session.questions_asked_total,
            turn_number=turn_number,
            allowed=True,
            denial_reason=None,
        )

    # ── Private helpers ──────────────────────────────────────────────────────

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
        )
