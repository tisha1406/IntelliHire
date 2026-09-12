"""
Phase 5 — Question Orchestration & Interview Turn Engine

QuestionDispatcher: The ONLY Phase 5 component allowed to mutate question-dispatch
fields on InterviewSessionSchema.

Strict mutation scope (Phase 5 boundary):
  MAY mutate:
    - session.questions_asked_total  (increment by 1)
    - session.topic_progress[matching].questions_asked  (increment by 1)
    - session.question_history  (append QuestionRecord)

  MUST NOT mutate:
    - session.state  (InterviewState — owned by Phase 4 RuntimeController)
    - topic_progress.state  (TopicState — owned by Phase 4 TopicStateManager)
    - topic_progress.qualitatively_covered  (owned by future Answer Evaluation phase)
    - topic_progress.structurally_attempted  (not Phase 5's authority)
    - session.current_topic_id  (owned by Phase 4)
    - InterviewBlueprint  (immutable — never mutated)

Atomic commit semantics:
  The dispatcher validates all preconditions, builds the QuestionRecord,
  then commits ALL mutations together in a defined order. If anything fails
  mid-commit, it rolls back already-applied mutations before raising
  QuestionDispatchError, ensuring the session remains consistent.

Idempotency note:
  turn_number = questions_asked_total + 1 is used as a stable turn identity.
  The caller (QuestionEngine) must not call dispatch() twice for the same turn.
  Future API-level idempotency can key on (session_id, turn_number) to detect
  duplicate HTTP retries without touching this layer.
"""
from typing import Optional

from app.ai_interview.question_engine.schemas import (
    GeneratedQuestion,
    QuestionRecord,
    QuestionTurnPlan,
)
from app.ai_interview.question_engine.exceptions import QuestionDispatchError
from app.ai_interview.schemas.session import InterviewSessionSchema, TopicProgress


class QuestionDispatcher:
    """
    Atomically commits a validated, duplicate-free question to session state.

    Call only after:
      1. QuestionValidator.validate() has passed.
      2. DuplicateDetector.check() has passed.

    Will raise QuestionDispatchError (with rollback) if any invariant is violated.
    """

    @staticmethod
    def dispatch(
        session: InterviewSessionSchema,
        plan: QuestionTurnPlan,
        question: GeneratedQuestion,
    ) -> QuestionRecord:
        """
        Commit the question to session state.

        Args:
            session:  Mutable InterviewSessionSchema.
            plan:     The approved QuestionTurnPlan for this turn.
            question: The validated, duplicate-free GeneratedQuestion.

        Returns:
            QuestionRecord — the officially recorded question.

        Raises:
            QuestionDispatchError: if session state is inconsistent or
                                   any mutation cannot be safely committed.
        """
        # ── Pre-dispatch invariant checks ─────────────────────────────────────
        QuestionDispatcher._assert_pre_dispatch_invariants(session, plan)

        # ── Resolve topic progress ────────────────────────────────────────────
        topic_progress: Optional[TopicProgress] = next(
            (p for p in session.topic_progress if p.topic_id == plan.topic_id),
            None,
        )
        if topic_progress is None:
            raise QuestionDispatchError(
                f"Cannot dispatch: TopicProgress for topic_id={plan.topic_id!r} "
                f"not found in session {session.session_id!r}."
            )

        # ── Build QuestionRecord ──────────────────────────────────────────────
        turn_number = session.questions_asked_total + 1
        record = QuestionRecord(
            session_id=session.session_id,
            turn_number=turn_number,
            topic_id=plan.topic_id,
            question_text=question.question_text,
            question_type=question.question_type,
            difficulty=question.difficulty,
        )

        # ── Atomic commit (ordered, with rollback on failure) ─────────────────
        # Snapshot pre-mutation state for rollback.
        snapshot_total = session.questions_asked_total
        snapshot_topic_count = topic_progress.questions_asked
        history_len_before = len(session.question_history)

        try:
            # Step 1: Append to question history
            session.question_history.append(record)

            # Step 2: Increment per-topic counter
            topic_progress.questions_asked += 1

            # Step 3: Increment global counter
            session.questions_asked_total += 1

            # Step 4: Post-dispatch invariant verification
            QuestionDispatcher._assert_post_dispatch_invariants(
                session, topic_progress, snapshot_total, snapshot_topic_count
            )

        except Exception as exc:
            # Rollback all mutations to keep session consistent.
            session.questions_asked_total = snapshot_total
            topic_progress.questions_asked = snapshot_topic_count
            # Remove the appended record if it was added
            if len(session.question_history) > history_len_before:
                session.question_history = session.question_history[:history_len_before]
            raise QuestionDispatchError(
                f"Dispatch failed and was rolled back for session {session.session_id!r}, "
                f"turn {turn_number}. Cause: {exc}"
            ) from exc

        return record

    # ── Private invariant checkers ────────────────────────────────────────────

    @staticmethod
    def _assert_pre_dispatch_invariants(
        session: InterviewSessionSchema,
        plan: QuestionTurnPlan,
    ) -> None:
        """Check session consistency before any mutation."""
        from app.ai_interview.core.enums import InterviewState

        if session.state != InterviewState.IN_PROGRESS:
            raise QuestionDispatchError(
                f"Cannot dispatch: session {session.session_id!r} is in state "
                f"{session.state.value!r}, expected IN_PROGRESS."
            )

        if session.questions_asked_total != plan.total_questions_asked:
            raise QuestionDispatchError(
                f"Counter drift detected before dispatch: "
                f"session.questions_asked_total={session.questions_asked_total}, "
                f"plan.total_questions_asked={plan.total_questions_asked}. "
                f"A concurrent dispatch may have occurred."
            )

        if session.questions_asked_total >= session.blueprint.total_question_budget:
            raise QuestionDispatchError(
                f"Global budget already exhausted ({session.questions_asked_total} >= "
                f"{session.blueprint.total_question_budget}). Dispatch aborted."
            )

    @staticmethod
    def _assert_post_dispatch_invariants(
        session: InterviewSessionSchema,
        topic_progress: TopicProgress,
        pre_total: int,
        pre_topic: int,
    ) -> None:
        """Verify mutations are exactly +1 increments (no partial / double increment)."""
        expected_total = pre_total + 1
        expected_topic = pre_topic + 1

        if session.questions_asked_total != expected_total:
            raise RuntimeError(
                f"Post-dispatch invariant violation: expected questions_asked_total="
                f"{expected_total}, got {session.questions_asked_total}."
            )

        if topic_progress.questions_asked != expected_topic:
            raise RuntimeError(
                f"Post-dispatch invariant violation: expected topic questions_asked="
                f"{expected_topic}, got {topic_progress.questions_asked}."
            )
