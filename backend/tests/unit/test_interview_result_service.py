"""
tests/unit/test_interview_result_service.py
Unit tests for the rewritten InterviewResultService.
Uses mocked InterviewSessionRepository - no MongoDB needed.

Import note: QuestionRecord is imported directly from the sub-module
(not via the question_engine package __init__.py) to avoid the circular
import that occurs when QuestionEngine loads at module initialization time.
"""
import uuid
import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

from app.ai_interview.core.enums import (
    InterviewState, DifficultyLevel, QuestionType, TopicState,
    ResumeEvidence, InterviewEvidence, RequirementCriticality,
    QuestionCategory, TopicTerminalReason,
)
from app.ai_interview.answer_engine.enums import CoverageSignal, FollowUpSignal
from app.ai_interview.answer_engine.schemas import EvaluationRecord
from app.ai_interview.schemas.session import (
    InterviewSessionSchema, TopicProgress, TopicEvaluationAggregate,
)
from app.ai_interview.schemas.blueprint import InterviewBlueprint, TopicBlueprint
from app.ai_interview.persistence.exceptions import SessionNotFoundError
from app.services.interview_result_service import InterviewResultService, _to_100


# QuestionRecord must be imported lazily or from the schemas module directly
# to avoid the circular import through question_engine/__init__.py.
def _get_qr_class():
    import importlib
    m = importlib.import_module("app.ai_interview.question_engine.schemas")
    return m.QuestionRecord


# ---------------------------------------------------------------------------
# Factories
# ---------------------------------------------------------------------------

def _make_blueprint(topics):
    n = max(1, len(topics))
    return InterviewBlueprint(
        blueprint_version="1", total_question_budget=n * 2,
        min_questions=n, max_questions=n * 3, emergency_max_questions=n * 4,
        topics=topics,
    )


def _make_session(state=InterviewState.COMPLETED, question_history=None,
                  evaluation_history=None, topic_progress=None,
                  blueprint_topics=None, completed_at=None):
    blueprint_topics = blueprint_topics or []
    return InterviewSessionSchema(
        session_id="s1", candidate_id="c1", company_id="co1", campaign_id="cam1",
        mode_id="technical", mode_version=1, state=state,
        blueprint=_make_blueprint(blueprint_topics),
        topic_progress=topic_progress or [],
        question_history=question_history or [],
        evaluation_history=evaluation_history or [],
        version=3, created_at=datetime.now(timezone.utc),
        completed_at=completed_at or (
            datetime.now(timezone.utc) if state == InterviewState.COMPLETED else None
        ),
    )


def _tb(tid, tname):
    return TopicBlueprint(topic_id=tid, topic_name=tname, source="resume", priority=1,
        initial_difficulty=DifficultyLevel.MEDIUM,
        allowed_question_types=[QuestionType.INITIAL], question_budget=2)


def _qr(rid, tid, text, turn_number=1, category=None):
    QR = _get_qr_class()
    return QR(record_id=rid, session_id="s1", turn_number=turn_number, topic_id=tid,
        question_text=text, question_type=QuestionType.INITIAL,
        difficulty=DifficultyLevel.MEDIUM, category=category)


def _er(qid, tid, sc=0.8, cov=CoverageSignal.QUALITATIVELY_COVERED,
        fu=FollowUpSignal.NONE):
    return EvaluationRecord(evaluation_id=str(uuid.uuid4()), question_record_id=qid,
        topic_id=tid, overall_score=sc, qualitative_coverage_signal=cov,
        follow_up_signal=fu, timestamp=datetime.now(timezone.utc))


def _mtp(tid, n=1, cum=0.8, strong=0, partial=0, weak=0, ins=0, covered=True,
         resume_evidence=None, candidate_claim=None, interview_evidence=None,
         follow_up_count=0, criticality=None, terminal_reason=None, questions_asked=None):
    agg = TopicEvaluationAggregate(answers_evaluated=n, cumulative_score=cum,
        average_score=cum / n if n else 0.0, strong_answers=strong,
        partial_answers=partial, weak_answers=weak, insufficient_answers=ins)
    return TopicProgress(topic_id=tid,
        state=TopicState.COVERED if covered else TopicState.IN_PROGRESS,
        structurally_attempted=True, qualitatively_covered=covered,
        coverage_score=agg.average_score, readiness_score=agg.average_score,
        questions_asked=n if questions_asked is None else questions_asked,
        evaluation_aggregate=agg,
        resume_evidence=resume_evidence, candidate_claim=candidate_claim,
        interview_evidence=interview_evidence, follow_up_count=follow_up_count,
        criticality=criticality, terminal_reason=terminal_reason)


def _svc(session):
    s = InterviewResultService.__new__(InterviewResultService)
    m = MagicMock()
    m.get_by_id = AsyncMock(return_value=session)
    s._engine_repo = m
    return s


def _svc404():
    s = InterviewResultService.__new__(InterviewResultService)
    m = MagicMock()
    m.get_by_id = AsyncMock(side_effect=SessionNotFoundError("nf"))
    s._engine_repo = m
    return s


BANNED = [
    "communication_score", "confidence", "problem_solving",
    "soft_skills_score", "time_management", "resume_match",
    "radar_data", "technical_score",
]

# ---------------------------------------------------------------------------
# TEST 1 - Single question, report generated, overall score correct
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_01_single_question_report():
    q = _qr("q1", "py", "Explain decorators")
    ev = _er("q1", "py", 0.8)
    tp = _mtp("py", 1, 0.8, strong=1)
    s = _make_session(question_history=[q], evaluation_history=[ev],
                      topic_progress=[tp], blueprint_topics=[_tb("py", "Python")])
    r = await _svc(s).generate_result_report("s1")
    assert r["has_report"] is True
    assert r["overall_score"] == 80
    assert r["question_feedback"][0]["topic"] == "Python"
    assert r["question_feedback"][0]["score"] == 0.8
    assert r["question_feedback"][0]["question"] == "Explain decorators"


# ---------------------------------------------------------------------------
# TEST 2 - Multi-question aggregation, no hardcoded scores
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_02_multi_question_aggregation_no_hardcoded():
    scores = [0.6, 0.9, 0.3]
    qs = [_qr(f"q{i}", "py", f"Q{i}") for i in range(3)]
    evs = [_er(f"q{i}", "py", s) for i, s in enumerate(scores)]
    tp = _mtp("py", 3, sum(scores), strong=1, partial=1, weak=1)
    s = _make_session(question_history=qs, evaluation_history=evs,
                      topic_progress=[tp], blueprint_topics=[_tb("py", "Python")])
    r = await _svc(s).generate_result_report("s1")
    expected = round(sum(scores) / 3 * 100)
    assert r["overall_score"] == expected
    assert r["question_count"] == 3
    for k in BANNED:
        assert k not in r, f"Hardcoded mock key '{k}' found in report"


# ---------------------------------------------------------------------------
# TEST 3 - Multiple topics, topic scores correct
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_03_multi_topic_scores():
    bps = [_tb("py", "Python"), _tb("sd", "System Design")]
    qs = [_qr("q1", "py", "Py Q"), _qr("q2", "sd", "SD Q")]
    evs = [_er("q1", "py", 0.9), _er("q2", "sd", 0.5)]
    tps = [_mtp("py", 1, 0.9, strong=1), _mtp("sd", 1, 0.5, partial=1)]
    s = _make_session(question_history=qs, evaluation_history=evs,
                      topic_progress=tps, blueprint_topics=bps)
    r = await _svc(s).generate_result_report("s1")
    ts = {t["topic_id"]: t for t in r["topic_scores"]}
    assert ts["py"]["score_100"] == 90
    assert ts["sd"]["score_100"] == 50
    assert ts["py"]["topic_name"] == "Python"
    assert ts["sd"]["topic_name"] == "System Design"


# ---------------------------------------------------------------------------
# TEST 4 - Strengths and weaknesses from real evaluation data
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_04_strengths_and_weaknesses_from_real_data():
    bps = [_tb("py", "Python"), _tb("db", "Databases")]
    qs = [_qr("qs", "py", "Py"), _qr("qw", "db", "DB")]
    evs = [_er("qs", "py", 0.9), _er("qw", "db", 0.3)]
    tps = [_mtp("py", 1, 0.9, strong=1), _mtp("db", 1, 0.3, weak=1, covered=False)]
    s = _make_session(question_history=qs, evaluation_history=evs,
                      topic_progress=tps, blueprint_topics=bps)
    r = await _svc(s).generate_result_report("s1")
    assert any("Python" in x for x in r["strengths"]), r["strengths"]
    assert any("Databases" in x for x in r["weaknesses"]), r["weaknesses"]
    # Must not be the default fallback when real data exists
    assert r["strengths"] != ["Completed all interview questions"]


# ---------------------------------------------------------------------------
# TEST 5 - Completed session with no evaluations -> safe behavior
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_05_completed_no_evaluations():
    s = _make_session()
    r = await _svc(s).generate_result_report("s1")
    assert r["has_report"] is False
    assert r["status"] == "COMPLETED_NO_DATA"


# ---------------------------------------------------------------------------
# TEST 6 - Session not found -> correct error
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_06_session_not_found():
    with pytest.raises(ValueError, match="not found"):
        await _svc404().generate_result_report("nonexistent")


# ---------------------------------------------------------------------------
# TEST 7 - No hardcoded mock scores present in returned report
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_07_no_hardcoded_mock_scores():
    q = _qr("q1", "py", "Q")
    ev = _er("q1", "py", 0.7)
    tp = _mtp("py", 1, 0.7, partial=1)
    s = _make_session(question_history=[q], evaluation_history=[ev],
                      topic_progress=[tp], blueprint_topics=[_tb("py", "Python")])
    r = await _svc(s).generate_result_report("s1")
    for k in BANNED:
        assert k not in r, f"Banned mock field '{k}' must not appear in report"
    # overall_score must be derived from real data, not a hardcoded magic number
    assert r["overall_score"] == 70, f"Expected 70, got {r['overall_score']}"


# ---------------------------------------------------------------------------
# TEST 8 - Candidate receives real calculated interviewScore
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_08_candidate_update_receives_real_score():
    scores = [0.6, 0.8]
    qs = [_qr(f"q{i}", "py", f"Q{i}") for i in range(2)]
    evs = [_er(f"q{i}", "py", s) for i, s in enumerate(scores)]
    tp = _mtp("py", 2, sum(scores), strong=1, partial=1)
    s = _make_session(question_history=qs, evaluation_history=evs,
                      topic_progress=[tp], blueprint_topics=[_tb("py", "Python")])
    r = await _svc(s).generate_result_report("s1")
    expected = _to_100(sum(scores) / len(scores))
    assert r["overall_score"] == expected
    assert r["has_report"] is True


# ---------------------------------------------------------------------------
# TEST 9 - IN_PROGRESS session returns correct has_report=False status
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_09_incomplete_session_returns_in_progress():
    s = _make_session(state=InterviewState.IN_PROGRESS, completed_at=None)
    r = await _svc(s).generate_result_report("s1")
    assert r["has_report"] is False
    assert r["status"] == "IN_PROGRESS"


# ---------------------------------------------------------------------------
# Unit test: _to_100 conversion helper
# ---------------------------------------------------------------------------

def test_to_100_clamping():
    assert _to_100(0.0) == 0
    assert _to_100(1.0) == 100
    assert _to_100(0.5) == 50
    assert _to_100(1.5) == 100   # clamp above 1.0
    assert _to_100(-0.1) == 0   # clamp below 0.0
    assert _to_100(0.855) == 86  # rounding


# ===========================================================================
# D-01 — Evidence model tests
# ===========================================================================

# ---------------------------------------------------------------------------
# D-01 TEST 1 - A fully-populated topic exposes resume_evidence,
# candidate_claim, interview_evidence, final_assessment, and the actual
# dispatched question records.
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_d01_01_topic_exposes_full_evidence_model():
    q = _qr("q1", "docker", "How would you reduce a Docker image's size?", turn_number=1)
    ev = _er("q1", "docker", 0.85)
    tp = _mtp(
        "docker", n=1, cum=0.85, strong=1,
        resume_evidence=ResumeEvidence.PARTIAL,
        candidate_claim="I used Docker in a side project",
        interview_evidence=InterviewEvidence.STRONG,
    )
    s = _make_session(question_history=[q], evaluation_history=[ev],
                      topic_progress=[tp], blueprint_topics=[_tb("docker", "Docker")])
    r = await _svc(s).generate_result_report("s1")

    # --- Correction: topic_scores[].questions_asked stays the existing INT
    # count, completely unchanged by D-01. ---
    score_topic = r["topic_scores"][0]
    assert score_topic["questions_asked"] == 1
    assert isinstance(score_topic["questions_asked"], int)
    assert score_topic["score_100"] == 85
    assert "resume_evidence" not in score_topic  # evidence fields live in topic_evidence, not here

    # --- The new per-topic evidence block, in its own sibling list. ---
    evidence_topic = r["topic_evidence"][0]
    assert evidence_topic["resume_evidence"] == "partial"
    assert evidence_topic["candidate_claim"] == "I used Docker in a side project"
    assert evidence_topic["interview_evidence"] == "strong"
    assert evidence_topic["final_assessment"] == "strong"  # average_score 0.85 >= 0.8

    # The required field name is exactly "questions_asked", as a LIST here —
    # a different container from topic_scores[].questions_asked above.
    assert isinstance(evidence_topic["questions_asked"], list)
    assert len(evidence_topic["questions_asked"]) == 1
    assert evidence_topic["questions_asked"][0]["question_text"] == q.question_text
    assert evidence_topic["questions_asked"][0]["record_id"] == "q1"


# ---------------------------------------------------------------------------
# D-01 TEST 2 - Follow-up tracking: followup_depth and
# followup_categories_used are correctly derived from real dispatched records.
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_d01_02_followup_depth_and_categories():
    qs = [
        _qr("q1", "py", "Explain decorators.", turn_number=1, category=QuestionCategory.NEW),
        _qr("q2", "py", "Why that approach?", turn_number=2, category=QuestionCategory.FOLLOWUP_DEPTH),
        _qr("q3", "py", "Give a concrete example.", turn_number=3, category=QuestionCategory.FOLLOWUP_EVIDENCE),
    ]
    evs = [_er("q1", "py", 0.6), _er("q2", "py", 0.7), _er("q3", "py", 0.8)]
    tp = _mtp("py", n=3, cum=2.1, follow_up_count=2)
    s = _make_session(question_history=qs, evaluation_history=evs,
                      topic_progress=[tp], blueprint_topics=[_tb("py", "Python")])
    r = await _svc(s).generate_result_report("s1")

    topic = r["topic_evidence"][0]
    assert topic["followup_depth"] == 2  # TopicProgress.follow_up_count, not a question-count inference
    assert topic["followup_categories_used"] == ["followup_depth", "followup_evidence"]
    assert len(topic["questions_asked"]) == 3
    # Order preserved by turn_number
    assert [q["record_id"] for q in topic["questions_asked"]] == ["q1", "q2", "q3"]
    # topic_scores' int count is unaffected by this restructuring.
    assert r["topic_scores"][0]["questions_asked"] == 3


@pytest.mark.asyncio
async def test_d01_02b_new_and_gap_verification_categories_are_not_followups():
    qs = [_qr("q1", "k8s", "I don't see Kubernetes on your resume...",
               turn_number=1, category=QuestionCategory.GAP_VERIFICATION)]
    evs = [_er("q1", "k8s", 0.4)]
    tp = _mtp("k8s", n=1, cum=0.4, follow_up_count=0)
    s = _make_session(question_history=qs, evaluation_history=evs,
                      topic_progress=[tp], blueprint_topics=[_tb("k8s", "Kubernetes")])
    r = await _svc(s).generate_result_report("s1")
    topic = r["topic_evidence"][0]
    assert topic["followup_categories_used"] == []  # GAP_VERIFICATION is not a follow-up category
    assert topic["followup_depth"] == 0


# ---------------------------------------------------------------------------
# D-01 TEST 3 - skip_reason is exposed only for topics that were never
# attempted, using the terminal_reason stamped at session completion.
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_d01_03_skip_reason_exposed_for_unattempted_topic():
    # "react" was evaluated normally; "rust" was never reached (questions_asked=0)
    # and was stamped BUDGET_EXHAUSTED by RuntimeController.execute_transition
    # at session-completion time (the D-01 supporting change).
    q = _qr("q1", "react", "Explain React hooks.")
    ev = _er("q1", "react", 0.7)
    tp_reached = _mtp("react", n=1, cum=0.7, partial=1)
    tp_skipped = _mtp(
        "rust", n=0, cum=0.0, questions_asked=0,
        terminal_reason=TopicTerminalReason.BUDGET_EXHAUSTED,
    )
    s = _make_session(
        question_history=[q], evaluation_history=[ev],
        topic_progress=[tp_reached, tp_skipped],
        blueprint_topics=[_tb("react", "React"), _tb("rust", "Rust")],
    )
    r = await _svc(s).generate_result_report("s1")

    # "react" still only appears in topic_scores (unchanged existing
    # behavior: built from evaluated_topic_ids). "rust" was never evaluated,
    # so it correctly does not appear in topic_scores at all.
    assert len(r["topic_scores"]) == 1
    assert {t["topic_id"] for t in r["topic_scores"]} == {"react"}

    # topic_evidence, however, covers ALL topics (including never-reached
    # ones), so "rust"'s skip_reason is genuinely observable here.
    evidence_by_id = {t["topic_id"]: t for t in r["topic_evidence"]}
    assert set(evidence_by_id.keys()) == {"react", "rust"}
    assert evidence_by_id["react"]["skip_reason"] is None  # attempted -> no skip_reason
    assert evidence_by_id["react"]["questions_asked"] != []  # has real dispatched records
    assert evidence_by_id["rust"]["skip_reason"] == "budget_exhausted"
    assert evidence_by_id["rust"]["questions_asked"] == []  # never dispatched, never fabricated


def test_d01_03b_skip_reason_none_for_an_attempted_but_not_yet_terminal_topic():
    """A topic that WAS attempted (questions_asked > 0) must never get a
    fabricated skip_reason, even if terminal_reason happens to be unset."""
    tp = _mtp("py", n=1, cum=0.5, partial=1, questions_asked=1, terminal_reason=None)
    assert tp.questions_asked > 0 and tp.terminal_reason is None
    # (Exercised indirectly via _build_topic_evidence through the async tests
    # above; this is a direct sanity check of the TopicProgress fixture itself.)


# ---------------------------------------------------------------------------
# D-01 TEST 4 - Session-level requirement-coverage summary: critical/required/
# preferred/resume-only topics are correctly tallied, and a candidate_claim
# alone never counts as "verified".
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_d01_04_requirement_coverage_summary():
    qs = [
        _qr("q1", "critical_verified", "Q1"),
        _qr("q2", "critical_claim_only", "Q2"),
        _qr("q3", "preferred_weak", "Q3"),
    ]
    evs = [
        _er("q1", "critical_verified", 0.9),
        _er("q2", "critical_claim_only", 0.3),
        _er("q3", "preferred_weak", 0.4),
    ]
    tps = [
        # Genuinely verified via real interview_evidence + qualitatively_covered.
        _mtp("critical_verified", n=1, cum=0.9, strong=1, covered=True,
             criticality=RequirementCriticality.CRITICAL,
             interview_evidence=InterviewEvidence.STRONG),
        # Candidate claimed experience, but interview_evidence/coverage don't
        # back it up -> must NOT count as verified.
        _mtp("critical_claim_only", n=1, cum=0.3, weak=1, covered=False,
             criticality=RequirementCriticality.CRITICAL,
             candidate_claim="I have used this for years",
             interview_evidence=InterviewEvidence.BASIC),
        _mtp("preferred_weak", n=1, cum=0.4, weak=1, covered=False,
             criticality=RequirementCriticality.PREFERRED,
             interview_evidence=InterviewEvidence.BASIC),
        # Never reached at all.
        _mtp("resume_only_skipped", n=0, cum=0.0, questions_asked=0,
             criticality=RequirementCriticality.RESUME_ONLY,
             terminal_reason=TopicTerminalReason.DEPRIORITIZED),
    ]
    s = _make_session(
        question_history=qs, evaluation_history=evs, topic_progress=tps,
        blueprint_topics=[
            _tb("critical_verified", "A"), _tb("critical_claim_only", "B"),
            _tb("preferred_weak", "C"), _tb("resume_only_skipped", "D"),
        ],
    )
    r = await _svc(s).generate_result_report("s1")

    cov = r["requirement_coverage"]
    assert cov["total_topics"] == 4
    assert cov["total_verified"] == 1
    assert cov["total_not_verified"] == 2
    assert cov["total_never_reached"] == 1

    assert cov["by_criticality"]["critical"]["total"] == 2
    assert cov["by_criticality"]["critical"]["verified"] == 1
    assert cov["by_criticality"]["critical"]["not_verified"] == 1
    assert cov["by_criticality"]["preferred"]["not_verified"] == 1
    assert cov["by_criticality"]["resume_only"]["never_reached"] == 1


# ---------------------------------------------------------------------------
# D-01 TEST 5 - final_assessment: deterministic mapping, and proof it does
# NOT simply duplicate interview_evidence.
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_d01_05_final_assessment_deterministic_mapping():
    cases = [
        (0.9, "strong"),
        (0.8, "strong"),       # boundary
        (0.79, "acceptable"),
        (0.5, "acceptable"),   # boundary
        (0.49, "basic"),
        (0.3, "basic"),        # boundary
        (0.29, "insufficient"),
        (0.0, "insufficient"),
    ]
    for score, expected in cases:
        q = _qr("q1", "t", "Q")
        ev = _er("q1", "t", score)
        tp = _mtp("t", n=1, cum=score)
        s = _make_session(question_history=[q], evaluation_history=[ev],
                          topic_progress=[tp], blueprint_topics=[_tb("t", "Topic")])
        r = await _svc(s).generate_result_report("s1")
        assert r["topic_evidence"][0]["final_assessment"] == expected, (
            f"score={score} expected {expected} got {r['topic_evidence'][0]['final_assessment']}"
        )


@pytest.mark.asyncio
async def test_d01_05b_final_assessment_differs_from_interview_evidence():
    """A topic with STRONG interview_evidence (the most recent answer's
    signal) but a weak aggregate average (two weak answers, one strong) must
    get a DIFFERENT final_assessment -- proving this is a true rollup, not a
    duplicate of interview_evidence."""
    qs = [_qr(f"q{i}", "t", f"Q{i}", turn_number=i + 1) for i in range(3)]
    evs = [_er("q0", "t", 0.9), _er("q1", "t", 0.2), _er("q2", "t", 0.2)]
    tp = _mtp(
        "t", n=3, cum=1.3, strong=1, ins=2,
        interview_evidence=InterviewEvidence.STRONG,  # most recent signal only
    )
    s = _make_session(question_history=qs, evaluation_history=evs,
                      topic_progress=[tp], blueprint_topics=[_tb("t", "Topic")])
    r = await _svc(s).generate_result_report("s1")
    topic = r["topic_evidence"][0]
    assert topic["interview_evidence"] == "strong"
    assert topic["final_assessment"] == "basic"  # avg = (0.9+0.2+0.2)/3 = 0.433... -> basic
    assert topic["interview_evidence"] != topic["final_assessment"]


def test_d01_05c_final_assessment_not_demonstrated_for_zero_evaluations():
    tp = TopicProgress(topic_id="never_asked", questions_asked=0)
    from app.services.interview_result_service import _derive_final_assessment
    assert _derive_final_assessment(tp) == "not_demonstrated"


# ---------------------------------------------------------------------------
# D-01 TEST 6 - Existing report fields remain present alongside the new ones.
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_d01_06_existing_fields_unchanged():
    q = _qr("q1", "py", "Q")
    ev = _er("q1", "py", 0.7)
    tp = _mtp("py", n=1, cum=0.7, partial=1)
    s = _make_session(question_history=[q], evaluation_history=[ev],
                      topic_progress=[tp], blueprint_topics=[_tb("py", "Python")])
    r = await _svc(s).generate_result_report("s1")

    for key in [
        "session_id", "status", "has_report", "overall_score", "question_count",
        "completed_at", "question_feedback", "topic_scores", "strengths",
        "weaknesses", "improvement_suggestions", "company_remarks",
    ]:
        assert key in r, f"existing report key '{key}' is missing"

    # topic_scores itself must also keep its exact original keys, with
    # "questions_asked" still an int — the D-01 correction's core requirement.
    existing_topic_score_keys = {
        "topic_id", "topic_name", "questions_asked", "answers_evaluated",
        "average_score", "score_100", "strong_answers", "partial_answers",
        "weak_answers", "insufficient_answers", "qualitatively_covered", "coverage_score",
    }
    assert set(r["topic_scores"][0].keys()) == existing_topic_score_keys
    assert isinstance(r["topic_scores"][0]["questions_asked"], int)

    # requirement_coverage and topic_evidence are additive, not a replacement
    # of anything.
    assert "requirement_coverage" in r
    assert "topic_evidence" in r
    assert isinstance(r["topic_evidence"][0]["questions_asked"], list)


# ---------------------------------------------------------------------------
# D-01 TEST 7 - InterviewResultService makes no LLM call.
# ---------------------------------------------------------------------------

def test_d01_07_no_llm_call_imports_or_references():
    """Static proof: the report-aggregation module never imports or
    references any LLM provider/adapter/generator symbol."""
    import inspect
    from app.services import interview_result_service as svc_module
    source = inspect.getsource(svc_module)
    forbidden_terms = [
        "LLMProvider", "OpenAICompatibleAdapter", "generate_structured",
        "generate_text", "LLMQuestionGenerator", "LLMAnswerEvaluator", "groq", "openai",
    ]
    for term in forbidden_terms:
        assert term not in source, f"Found forbidden LLM-related reference '{term}' in InterviewResultService"
