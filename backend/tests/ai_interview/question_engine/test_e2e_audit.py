"""
Phase 5 — Architecture Audit: End-to-End Runtime Demonstration Tests

These tests complement the unit tests in test_question_engine.py.
They are specifically designed to verify the COMPLETE PIPELINE as a
realistic interview turn sequence, including:

  TEST A — Full pipeline (single turn)
  TEST B — Invalid → Valid retry (counter mutation audit)
  TEST C — Duplicate → Valid retry (no history pollution)
  TEST D — All retries fail (session completely unchanged)
  TEST E — Topic budget exhaustion with qualitative coverage audit
  TEST F — Blueprint immutability across multiple engine calls

AUDIT PRINCIPLE:
  These tests are not about coverage — they are about demonstrating that
  architectural invariants hold under realistic interview conditions.
  Each test asserts invariants EXPLICITLY, not just outcomes.
"""
import copy
import pytest
from datetime import datetime

from app.ai_interview.core.enums import (
    InterviewState, DifficultyLevel, QuestionType, TopicState,
)
from app.ai_interview.runtime.enums import RuntimeAction
from app.ai_interview.runtime.schemas import RuntimeDecision
from app.ai_interview.question_engine.question_engine import QuestionEngine
from app.ai_interview.question_engine.question_generator import FakeQuestionGenerator
from app.ai_interview.question_engine.enums import (
    QuestionEngineFailureCode, TurnDenialReason,
)
from app.ai_interview.question_engine.schemas import (
    GeneratedQuestion, QuestionRecord,
)
from app.ai_interview.schemas.session import InterviewSessionSchema, TopicProgress
from app.ai_interview.schemas.blueprint import InterviewBlueprint, TopicBlueprint


# ── Shared helpers ─────────────────────────────────────────────────────────────

def _run_turn(engine, session, runtime_decision, candidate_context, interview_mode):
    """Single convenience wrapper for one engine call."""
    return engine.request_next_question(
        session=session,
        runtime_decision=runtime_decision,
        candidate_context=candidate_context,
        mode=interview_mode,
    )


# ──────────────────────────────────────────────────────────────────────────────
# TEST A — Full pipeline: single successful question turn
#
# Verifies the complete pipeline executes correctly for one turn.
# Asserts EVERY state change and NO unexpected state change.
# ──────────────────────────────────────────────────────────────────────────────

class TestFullPipelineSingleTurn:
    """
    Audit: Complete pipeline for one interview turn.

    Phase 4 runtime authorises → Planner approves → Builder extracts evidence →
    Fake generator produces → Validator passes → Duplicate check passes →
    Dispatcher commits → Session mutated exactly.
    """

    def test_pipeline_snapshot_before_after(
        self, session_in_progress, runtime_decision_python, candidate_context, interview_mode
    ):
        """
        Snapshot all guarded session fields before and after one engine call.

        Exactly these changes expected:
          questions_asked_total: 0 → 1
          topic_progress[python].questions_asked: 0 → 1
          question_history: [] → [<one QuestionRecord>]

        Exactly these must NOT change:
          session.state
          topic_progress[python].state
          topic_progress[python].qualitatively_covered
          topic_progress[python].structurally_attempted
          blueprint (any field)
        """
        # --- Pre-call snapshot ---
        pre_total = session_in_progress.questions_asked_total
        pre_topic = session_in_progress.topic_progress[0].questions_asked
        pre_history_len = len(session_in_progress.question_history)
        pre_state = session_in_progress.state
        pre_topic_state = session_in_progress.topic_progress[0].state
        pre_qual_covered = session_in_progress.topic_progress[0].qualitatively_covered
        pre_struct_attempted = session_in_progress.topic_progress[0].structurally_attempted
        pre_blueprint_id = id(session_in_progress.blueprint)
        pre_total_budget = session_in_progress.blueprint.total_question_budget

        engine = QuestionEngine(generator=FakeQuestionGenerator(mode="valid"))
        result = _run_turn(engine, session_in_progress, runtime_decision_python,
                           candidate_context, interview_mode)

        # --- Result checks ---
        assert result.success is True
        assert result.question_record is not None
        assert result.question_sequence_number == 1
        assert result.attempts == 1
        assert result.failure_code is None
        assert result.topic_id == "python"

        # --- Exact expected mutations ---
        assert session_in_progress.questions_asked_total == pre_total + 1  # +1 only
        assert session_in_progress.topic_progress[0].questions_asked == pre_topic + 1  # +1 only
        assert len(session_in_progress.question_history) == pre_history_len + 1  # appended once

        # --- Exactly one QuestionRecord in history ---
        record = session_in_progress.question_history[0]
        assert record.session_id == session_in_progress.session_id
        assert record.turn_number == 1
        assert record.topic_id == "python"
        assert record.question_type == QuestionType.INITIAL  # first allowed type
        assert record.difficulty == DifficultyLevel.MEDIUM

        # --- Fields that MUST NOT change ---
        assert session_in_progress.state == pre_state  # InterviewState unchanged
        assert session_in_progress.topic_progress[0].state == pre_topic_state  # TopicState unchanged
        assert session_in_progress.topic_progress[0].qualitatively_covered == pre_qual_covered  # False
        assert session_in_progress.topic_progress[0].structurally_attempted == pre_struct_attempted
        # Blueprint object identity preserved (not replaced)
        assert id(session_in_progress.blueprint) == pre_blueprint_id
        # Blueprint budget value unchanged
        assert session_in_progress.blueprint.total_question_budget == pre_total_budget

    def test_question_record_is_official_history(
        self, session_in_progress, runtime_decision_python, candidate_context, interview_mode
    ):
        """The record returned by the engine == the record in session.question_history."""
        engine = QuestionEngine(generator=FakeQuestionGenerator(mode="valid"))
        result = _run_turn(engine, session_in_progress, runtime_decision_python,
                           candidate_context, interview_mode)

        assert result.success is True
        assert len(session_in_progress.question_history) == 1
        # Same object (by record_id, since Pydantic creates new instances on copy)
        history_record = session_in_progress.question_history[0]
        assert history_record.record_id == result.question_record.record_id
        assert history_record.question_text == result.question_record.question_text
        assert history_record.turn_number == result.question_record.turn_number


# ──────────────────────────────────────────────────────────────────────────────
# TEST B — Invalid → Valid retry
#
# Attempt 1: generator returns empty text (fails QuestionValidator)
# Attempt 2: generator returns valid text (passes all checks)
#
# AUDIT: counters increment EXACTLY ONCE (not on failed attempt)
# AUDIT: failed question text never appears in question_history
# ──────────────────────────────────────────────────────────────────────────────

class TestInvalidThenValidRetry:

    class _InvalidThenValidGenerator:
        """Returns invalid (empty) on attempt 1, valid on attempt 2."""
        def __init__(self):
            self.call_count = 0

        def generate(self, request, attempt_number=1):
            self.call_count += 1
            if self.call_count == 1:
                return GeneratedQuestion(
                    question_text="",  # fails validator (empty)
                    question_type=request.selected_question_type,
                    topic_id=request.topic_id,
                    difficulty=request.difficulty,
                )
            return GeneratedQuestion(
                question_text="[Retry] Explain Python's memory management in detail.",
                question_type=request.selected_question_type,
                topic_id=request.topic_id,
                difficulty=request.difficulty,
            )

    def test_failed_attempt_does_not_mutate_counters(
        self, session_in_progress, runtime_decision_python, candidate_context, interview_mode
    ):
        """
        After attempt 1 fails validation, counters must still be 0.
        After attempt 2 succeeds, counters must be exactly 1.
        """
        gen = self._InvalidThenValidGenerator()
        engine = QuestionEngine(generator=gen)

        # Snapshot before
        pre_total = session_in_progress.questions_asked_total
        pre_topic = session_in_progress.topic_progress[0].questions_asked

        result = _run_turn(engine, session_in_progress, runtime_decision_python,
                           candidate_context, interview_mode)

        assert result.success is True
        assert result.attempts == 2  # took 2 attempts
        assert gen.call_count == 2   # generator called exactly twice

        # CRITICAL: counters incremented exactly once (not twice, not zero)
        assert session_in_progress.questions_asked_total == pre_total + 1
        assert session_in_progress.topic_progress[0].questions_asked == pre_topic + 1

    def test_failed_attempt_not_in_history(
        self, session_in_progress, runtime_decision_python, candidate_context, interview_mode
    ):
        """
        The empty-text question from attempt 1 must NOT appear in question_history.
        Only the valid question from attempt 2 must be stored.
        """
        engine = QuestionEngine(generator=self._InvalidThenValidGenerator())
        result = _run_turn(engine, session_in_progress, runtime_decision_python,
                           candidate_context, interview_mode)

        assert result.success is True
        assert len(session_in_progress.question_history) == 1

        history_record = session_in_progress.question_history[0]
        # Must be the retry question, NOT the empty one
        assert history_record.question_text != ""
        assert "Retry" in history_record.question_text


# ──────────────────────────────────────────────────────────────────────────────
# TEST C — Duplicate → Valid retry
#
# Attempt 1: generator returns a duplicate of an existing history question
# Attempt 2: generator returns a genuinely unique question
#
# AUDIT: duplicate never stored in question_history
# AUDIT: counters only increment for the valid dispatch
# ──────────────────────────────────────────────────────────────────────────────

class TestDuplicateThenValidRetry:

    # Pre-seeded existing question text
    EXISTING_Q = "What is Python and why is it popular in data science?"

    def _make_seeded_session(self, session_in_progress):
        """Add one existing question to history to create the duplicate target."""
        existing = QuestionRecord(
            session_id=session_in_progress.session_id,
            turn_number=1,
            topic_id="python",
            question_text=self.EXISTING_Q,
            question_type=QuestionType.INITIAL,
            difficulty=DifficultyLevel.MEDIUM,
        )
        session_in_progress.question_history.append(existing)
        session_in_progress.questions_asked_total = 1
        session_in_progress.topic_progress[0].questions_asked = 1
        return session_in_progress

    def test_duplicate_rejected_then_unique_accepted(
        self, session_in_progress, runtime_decision_python, candidate_context, interview_mode
    ):
        """Attempt 1 duplicates existing history; attempt 2 succeeds with unique text."""
        session = self._make_seeded_session(session_in_progress)

        call_count = [0]

        class _DupThenUniqueGen:
            def generate(self_, request, attempt_number=1):
                call_count[0] += 1
                if call_count[0] == 1:
                    return GeneratedQuestion(
                        question_text=TestDuplicateThenValidRetry.EXISTING_Q,  # exact dup
                        question_type=request.selected_question_type,
                        topic_id=request.topic_id,
                        difficulty=request.difficulty,
                    )
                return GeneratedQuestion(
                    question_text="Explain Python decorators and provide a practical example.",
                    question_type=request.selected_question_type,
                    topic_id=request.topic_id,
                    difficulty=request.difficulty,
                )

        engine = QuestionEngine(generator=_DupThenUniqueGen())
        result = _run_turn(engine, session, runtime_decision_python,
                           candidate_context, interview_mode)

        assert result.success is True
        assert result.attempts == 2
        # history now has 2 entries: the pre-seeded one + the newly dispatched one
        assert len(session.question_history) == 2
        # The pre-seeded entry is still first
        assert session.question_history[0].question_text == self.EXISTING_Q
        # The second entry must NOT be the duplicate
        assert session.question_history[1].question_text != self.EXISTING_Q
        assert "decorator" in session.question_history[1].question_text.lower()

    def test_counters_after_duplicate_retry(
        self, session_in_progress, runtime_decision_python, candidate_context, interview_mode
    ):
        """Global and topic counters increment exactly once (for the valid dispatch)."""
        session = self._make_seeded_session(session_in_progress)
        pre_total = session.questions_asked_total  # = 1
        pre_topic = session.topic_progress[0].questions_asked  # = 1

        call_count = [0]

        class _DupThenUniqueGen:
            def generate(self_, request, attempt_number=1):
                call_count[0] += 1
                if call_count[0] == 1:
                    return GeneratedQuestion(
                        question_text=TestDuplicateThenValidRetry.EXISTING_Q,
                        question_type=request.selected_question_type,
                        topic_id=request.topic_id,
                        difficulty=request.difficulty,
                    )
                return GeneratedQuestion(
                    question_text="Describe Python's GIL and when it becomes a bottleneck.",
                    question_type=request.selected_question_type,
                    topic_id=request.topic_id,
                    difficulty=request.difficulty,
                )

        engine = QuestionEngine(generator=_DupThenUniqueGen())
        result = _run_turn(engine, session, runtime_decision_python,
                           candidate_context, interview_mode)

        assert result.success is True
        assert session.questions_asked_total == pre_total + 1  # +1 only
        assert session.topic_progress[0].questions_asked == pre_topic + 1  # +1 only


# ──────────────────────────────────────────────────────────────────────────────
# TEST D — All retries fail: session completely unchanged
#
# All MAX_GENERATION_ATTEMPTS produce invalid questions (empty text).
# The engine must return a failure result with ZERO session mutations.
# ──────────────────────────────────────────────────────────────────────────────

class TestAllRetriesFail:

    def test_session_completely_unchanged_after_exhaustion(
        self, session_in_progress, runtime_decision_python, candidate_context, interview_mode
    ):
        """
        After all generation attempts fail, the session must be in EXACTLY
        the same state as before the engine call.
        """
        from app.ai_interview.question_engine.config import QuestionEngineConfig

        # Take deep snapshot of mutable session fields
        pre_total = session_in_progress.questions_asked_total
        pre_topic_count = session_in_progress.topic_progress[0].questions_asked
        pre_history_len = len(session_in_progress.question_history)
        pre_state = session_in_progress.state
        pre_topic_state = session_in_progress.topic_progress[0].state
        pre_qual_covered = session_in_progress.topic_progress[0].qualitatively_covered
        pre_struct_attempted = session_in_progress.topic_progress[0].structurally_attempted

        engine = QuestionEngine(generator=FakeQuestionGenerator(mode="invalid"))
        result = _run_turn(engine, session_in_progress, runtime_decision_python,
                           candidate_context, interview_mode)

        # Result must signal failure
        assert result.success is False
        assert result.failure_code == QuestionEngineFailureCode.VALIDATION_FAILED
        assert result.attempts == QuestionEngineConfig.MAX_GENERATION_ATTEMPTS
        assert result.question_record is None

        # EVERY guarded field must be unchanged
        assert session_in_progress.questions_asked_total == pre_total
        assert session_in_progress.topic_progress[0].questions_asked == pre_topic_count
        assert len(session_in_progress.question_history) == pre_history_len
        assert session_in_progress.state == pre_state
        assert session_in_progress.topic_progress[0].state == pre_topic_state
        assert session_in_progress.topic_progress[0].qualitatively_covered == pre_qual_covered
        assert session_in_progress.topic_progress[0].structurally_attempted == pre_struct_attempted

    def test_generator_called_exactly_max_times(
        self, session_in_progress, runtime_decision_python, candidate_context, interview_mode
    ):
        """Generator is called exactly MAX_GENERATION_ATTEMPTS times, not fewer or more."""
        from app.ai_interview.question_engine.config import QuestionEngineConfig

        call_count = [0]

        class _CountingInvalidGen:
            def generate(self_, request, attempt_number=1):
                call_count[0] += 1
                return GeneratedQuestion(
                    question_text="",  # always invalid
                    question_type=request.selected_question_type,
                    topic_id=request.topic_id,
                    difficulty=request.difficulty,
                )

        engine = QuestionEngine(generator=_CountingInvalidGen())
        _run_turn(engine, session_in_progress, runtime_decision_python,
                  candidate_context, interview_mode)

        assert call_count[0] == QuestionEngineConfig.MAX_GENERATION_ATTEMPTS


# ──────────────────────────────────────────────────────────────────────────────
# TEST E — Topic budget exhaustion with qualitative coverage audit
#
# blueprint.python_topic.question_budget = 3
#
# Turn 1: allowed ✓
# Turn 2: allowed ✓
# Turn 3: allowed ✓
# Turn 4: DENIED (topic budget exhausted)
#
# After turn 3:
#   topic_progress.questions_asked == 3 (== budget)
#   topic_progress.qualitatively_covered == False  ← CRITICAL
#   topic_progress.state != TopicState.COVERED     ← CRITICAL
#
# Budget exhaustion ≠ topic evaluated.
# ──────────────────────────────────────────────────────────────────────────────

class TestTopicBudgetExhaustionWithQualitativeAudit:

    def test_three_questions_allowed_fourth_denied(
        self, session_in_progress, runtime_decision_python, candidate_context, interview_mode
    ):
        """python_topic.question_budget=3: questions 1,2,3 succeed; question 4 is denied."""
        engine = QuestionEngine(generator=FakeQuestionGenerator(mode="valid"))
        python_progress = session_in_progress.topic_progress[0]

        # Verify budget is 3 for this test to be meaningful
        python_blueprint = next(
            t for t in session_in_progress.blueprint.topics if t.topic_id == "python"
        )
        assert python_blueprint.question_budget == 3

        results = []
        for _ in range(4):  # attempt 4 questions against budget=3
            result = _run_turn(engine, session_in_progress, runtime_decision_python,
                               candidate_context, interview_mode)
            results.append(result)

        # First 3 must succeed
        assert results[0].success is True, "Question 1 should be allowed"
        assert results[1].success is True, "Question 2 should be allowed"
        assert results[2].success is True, "Question 3 should be allowed"

        # Fourth must be denied by the Planner (not dispatcher — Planner fires first)
        assert results[3].success is False, "Question 4 should be denied"
        assert results[3].failure_code == QuestionEngineFailureCode.TURN_NOT_ALLOWED

    def test_counter_after_budget_exhaustion(
        self, session_in_progress, runtime_decision_python, candidate_context, interview_mode
    ):
        """After 3 successful dispatches, counters reflect exactly 3."""
        engine = QuestionEngine(generator=FakeQuestionGenerator(mode="valid"))
        python_progress = session_in_progress.topic_progress[0]

        for _ in range(3):
            result = _run_turn(engine, session_in_progress, runtime_decision_python,
                               candidate_context, interview_mode)
            assert result.success is True

        assert python_progress.questions_asked == 3
        assert session_in_progress.questions_asked_total == 3

    def test_qualitative_coverage_never_set_by_budget_exhaustion(
        self, session_in_progress, runtime_decision_python, candidate_context, interview_mode
    ):
        """
        CRITICAL INVARIANT:
        Even after all topic questions are dispatched, qualitatively_covered
        must remain False. Budget exhaustion ≠ topic qualitatively evaluated.
        Only a future answer evaluation phase may set this.
        """
        engine = QuestionEngine(generator=FakeQuestionGenerator(mode="valid"))
        python_progress = session_in_progress.topic_progress[0]

        for _ in range(3):
            _run_turn(engine, session_in_progress, runtime_decision_python,
                      candidate_context, interview_mode)

        # CRITICAL assertions
        assert python_progress.qualitatively_covered is False, (
            "qualitatively_covered MUST remain False after budget exhaustion. "
            "This field is owned by the future Answer Evaluation phase."
        )

    def test_topic_state_never_set_to_covered_by_budget_exhaustion(
        self, session_in_progress, runtime_decision_python, candidate_context, interview_mode
    ):
        """
        TopicState.COVERED must never be set by Phase 5.
        Phase 4 TopicStateManager is the only authority for TopicState transitions.
        """
        engine = QuestionEngine(generator=FakeQuestionGenerator(mode="valid"))
        python_progress = session_in_progress.topic_progress[0]
        original_topic_state = python_progress.state

        for _ in range(3):
            _run_turn(engine, session_in_progress, runtime_decision_python,
                      candidate_context, interview_mode)

        # Phase 5 MUST NOT set TopicState.COVERED
        assert python_progress.state != TopicState.COVERED, (
            "TopicState.COVERED MUST NOT be set by Phase 5. "
            "TopicState transitions are owned by Phase 4 TopicStateManager."
        )
        # The topic state should remain exactly as Phase 4 left it
        assert python_progress.state == original_topic_state, (
            f"Topic state was {original_topic_state.value!r} before and should remain so after dispatch. "
            f"Got: {python_progress.state.value!r}"
        )

    def test_turn_sequence_numbers_are_consecutive(
        self, session_in_progress, runtime_decision_python, candidate_context, interview_mode
    ):
        """turn_number must be 1, 2, 3 for three consecutive dispatches."""
        engine = QuestionEngine(generator=FakeQuestionGenerator(mode="valid"))

        records = []
        for _ in range(3):
            result = _run_turn(engine, session_in_progress, runtime_decision_python,
                               candidate_context, interview_mode)
            assert result.success is True
            records.append(result.question_record)

        assert records[0].turn_number == 1
        assert records[1].turn_number == 2
        assert records[2].turn_number == 3


# ──────────────────────────────────────────────────────────────────────────────
# TEST F — Blueprint immutability
#
# InterviewBlueprint must remain identical before and after all engine calls.
# Phase 5 reads the blueprint but must never modify it.
# ──────────────────────────────────────────────────────────────────────────────

class TestBlueprintImmutability:

    def _snapshot_blueprint(self, blueprint: InterviewBlueprint) -> dict:
        """Capture all blueprint field values as a plain dict."""
        return {
            "blueprint_version": blueprint.blueprint_version,
            "total_question_budget": blueprint.total_question_budget,
            "min_questions": blueprint.min_questions,
            "max_questions": blueprint.max_questions,
            "topics": [
                {
                    "topic_id": t.topic_id,
                    "topic_name": t.topic_name,
                    "priority": t.priority,
                    "mandatory": t.mandatory,
                    "question_budget": t.question_budget,
                    "initial_difficulty": t.initial_difficulty,
                    "allowed_question_types": list(t.allowed_question_types),
                }
                for t in blueprint.topics
            ],
        }

    def test_blueprint_unchanged_after_single_dispatch(
        self, session_in_progress, runtime_decision_python, candidate_context, interview_mode
    ):
        blueprint = session_in_progress.blueprint
        snapshot_before = self._snapshot_blueprint(blueprint)

        engine = QuestionEngine(generator=FakeQuestionGenerator(mode="valid"))
        _run_turn(engine, session_in_progress, runtime_decision_python,
                  candidate_context, interview_mode)

        snapshot_after = self._snapshot_blueprint(blueprint)
        assert snapshot_before == snapshot_after, (
            "Blueprint was mutated by Phase 5. This is a critical architectural violation."
        )

    def test_blueprint_unchanged_after_full_budget_exhaustion(
        self, session_in_progress, runtime_decision_python, candidate_context, interview_mode
    ):
        """Run 3 dispatches + 1 denied turn and verify blueprint is intact."""
        blueprint = session_in_progress.blueprint
        snapshot_before = self._snapshot_blueprint(blueprint)

        engine = QuestionEngine(generator=FakeQuestionGenerator(mode="valid"))
        for _ in range(4):  # 3 successful + 1 denied
            _run_turn(engine, session_in_progress, runtime_decision_python,
                      candidate_context, interview_mode)

        snapshot_after = self._snapshot_blueprint(blueprint)
        assert snapshot_before == snapshot_after, (
            "Blueprint was mutated during budget exhaustion sequence. Critical violation."
        )

    def test_blueprint_topic_budget_unchanged(
        self, session_in_progress, runtime_decision_python, candidate_context, interview_mode
    ):
        """
        topic_blueprint.question_budget must remain exactly as initialised.
        It must NOT be decremented or otherwise modified by dispatch.
        """
        python_blueprint = next(
            t for t in session_in_progress.blueprint.topics if t.topic_id == "python"
        )
        original_budget = python_blueprint.question_budget  # 3

        engine = QuestionEngine(generator=FakeQuestionGenerator(mode="valid"))
        for _ in range(3):
            _run_turn(engine, session_in_progress, runtime_decision_python,
                      candidate_context, interview_mode)

        # budget field must not have been consumed/decremented
        assert python_blueprint.question_budget == original_budget, (
            f"TopicBlueprint.question_budget was mutated: "
            f"expected {original_budget}, got {python_blueprint.question_budget}."
        )


# ──────────────────────────────────────────────────────────────────────────────
# Extra: Phase 4 authority verification
#
# Verify that Phase 5 never internally calls RuntimeController.
# Verify that session.state and current_topic_id are untouched.
# ──────────────────────────────────────────────────────────────────────────────

class TestPhase4AuthorityBoundary:

    def test_phase5_does_not_change_interview_state(
        self, session_in_progress, runtime_decision_python, candidate_context, interview_mode
    ):
        """InterviewState is owned by Phase 4 RuntimeController. Phase 5 must not touch it."""
        original_state = session_in_progress.state

        engine = QuestionEngine(generator=FakeQuestionGenerator(mode="valid"))
        # Multiple calls including one that should fail
        for _ in range(4):
            _run_turn(engine, session_in_progress, runtime_decision_python,
                      candidate_context, interview_mode)

        assert session_in_progress.state == original_state

    def test_phase5_does_not_change_current_topic_id(
        self, session_in_progress, runtime_decision_python, candidate_context, interview_mode
    ):
        """current_topic_id is owned by Phase 4. Phase 5 consumes it but never writes it."""
        original_topic_id = session_in_progress.current_topic_id

        engine = QuestionEngine(generator=FakeQuestionGenerator(mode="valid"))
        for _ in range(3):
            _run_turn(engine, session_in_progress, runtime_decision_python,
                      candidate_context, interview_mode)

        assert session_in_progress.current_topic_id == original_topic_id

    def test_completion_decision_not_made_by_engine(
        self, session_in_progress, runtime_decision_python, candidate_context, interview_mode
    ):
        """
        The QuestionEngine must return a structured result and leave completion
        decisions entirely to Phase 4. After budget exhaustion, the engine
        returns failure — it does NOT transition session.state to COMPLETED.
        """
        engine = QuestionEngine(generator=FakeQuestionGenerator(mode="valid"))

        # Exhaust topic budget
        for _ in range(4):
            _run_turn(engine, session_in_progress, runtime_decision_python,
                      candidate_context, interview_mode)

        # Phase 5 must NOT have transitioned to COMPLETED
        assert session_in_progress.state != InterviewState.COMPLETED, (
            "QuestionEngine must not transition session to COMPLETED. "
            "Completion is owned by Phase 4 CompletionEngine."
        )
        assert session_in_progress.state == InterviewState.IN_PROGRESS
