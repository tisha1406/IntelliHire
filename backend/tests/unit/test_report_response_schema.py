"""
D-02 regression tests.

Proves ReportResponse (backend/app/schemas/candidate_portal.py) accurately
describes the LIVE output of InterviewResultService.generate_result_report()
after D-01, including topic_evidence/requirement_coverage and the exact
"questions_asked" int-vs-list split between topic_scores and topic_evidence.

Builds a REAL InterviewSessionSchema and calls the real service (with only
its MongoDB repository mocked) to get a genuine report dict, then validates
it through ReportResponse — not a hand-written stand-in dict, so this would
fail if the schema and the service ever drift apart again.
"""
import uuid
import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from pydantic import ValidationError

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
from app.services.interview_result_service import InterviewResultService
from app.schemas.candidate_portal import ReportResponse


def _get_qr_class():
    import importlib
    return importlib.import_module("app.ai_interview.question_engine.schemas").QuestionRecord


def _make_blueprint(topics):
    n = max(1, len(topics))
    return InterviewBlueprint(
        blueprint_version="1", total_question_budget=n * 3,
        min_questions=n, max_questions=n * 4, emergency_max_questions=n * 5,
        topics=topics,
    )


def _make_session(question_history, evaluation_history, topic_progress, blueprint_topics):
    return InterviewSessionSchema(
        session_id="s1", candidate_id="c1", company_id="co1", campaign_id="cam1",
        mode_id="technical", mode_version=1, state=InterviewState.COMPLETED,
        blueprint=_make_blueprint(blueprint_topics),
        topic_progress=topic_progress, question_history=question_history,
        evaluation_history=evaluation_history,
        version=3, created_at=datetime.now(timezone.utc),
        completed_at=datetime.now(timezone.utc),
    )


def _tb(tid, tname):
    return TopicBlueprint(topic_id=tid, topic_name=tname, source="resume", priority=1,
        initial_difficulty=DifficultyLevel.MEDIUM,
        allowed_question_types=[QuestionType.INITIAL], question_budget=3)


def _qr(rid, tid, text, turn_number=1, category=None):
    QR = _get_qr_class()
    return QR(record_id=rid, session_id="s1", turn_number=turn_number, topic_id=tid,
        question_text=text, question_type=QuestionType.INITIAL,
        difficulty=DifficultyLevel.MEDIUM, category=category)


def _er(qid, tid, sc=0.8):
    return EvaluationRecord(evaluation_id=str(uuid.uuid4()), question_record_id=qid,
        topic_id=tid, overall_score=sc,
        qualitative_coverage_signal=CoverageSignal.QUALITATIVELY_COVERED,
        follow_up_signal=FollowUpSignal.NONE, timestamp=datetime.now(timezone.utc))


async def _real_report_dict():
    """Builds a session exercising every D-01 field, then calls the REAL
    InterviewResultService.generate_result_report() (mocking only the Mongo
    repository) to get a genuine report dict."""
    qs = [
        _qr("q1", "docker", "Reduce image size?", turn_number=1, category=QuestionCategory.NEW),
        _qr("q2", "docker", "Why that approach?", turn_number=2, category=QuestionCategory.FOLLOWUP_DEPTH),
    ]
    evs = [_er("q1", "docker", 0.85), _er("q2", "docker", 0.9)]
    tp_reached = TopicProgress(
        topic_id="docker", state=TopicState.COVERED, structurally_attempted=True,
        qualitatively_covered=True, coverage_score=0.875, readiness_score=0.875,
        questions_asked=2, follow_up_count=1,
        criticality=RequirementCriticality.CRITICAL,
        resume_evidence=ResumeEvidence.PARTIAL,
        candidate_claim="Used Docker in a side project",
        interview_evidence=InterviewEvidence.STRONG,
        evaluation_aggregate=TopicEvaluationAggregate(
            answers_evaluated=2, cumulative_score=1.75, average_score=0.875,
            strong_answers=2,
        ),
    )
    tp_skipped = TopicProgress(
        topic_id="rust", state=TopicState.NOT_STARTED, questions_asked=0,
        criticality=RequirementCriticality.RESUME_ONLY,
        terminal_reason=TopicTerminalReason.DEPRIORITIZED,
    )
    session = _make_session(
        question_history=qs, evaluation_history=evs,
        topic_progress=[tp_reached, tp_skipped],
        blueprint_topics=[_tb("docker", "Docker"), _tb("rust", "Rust")],
    )

    svc = InterviewResultService.__new__(InterviewResultService)
    mock_repo = MagicMock()
    mock_repo.get_by_id = AsyncMock(return_value=session)
    svc._engine_repo = mock_repo
    return await svc.generate_result_report("s1")


@pytest.mark.asyncio
async def test_real_completed_report_validates_against_report_response():
    """The core D-02 proof: a genuine, full-featured service output (not a
    hand-written stand-in) must validate without error."""
    report = await _real_report_dict()
    validated = ReportResponse.model_validate(report)  # must not raise

    assert validated.status == "COMPLETED"
    assert validated.has_report is True

    # topic_scores[].questions_asked stays an int (pre-existing field, D-01/D-02 untouched).
    docker_score = next(t for t in validated.topic_scores if t.topic_id == "docker")
    assert isinstance(docker_score.questions_asked, int)
    assert docker_score.questions_asked == 2

    # topic_evidence[].questions_asked is the detailed list, a different field.
    docker_evidence = next(t for t in validated.topic_evidence if t.topic_id == "docker")
    assert isinstance(docker_evidence.questions_asked, list)
    assert len(docker_evidence.questions_asked) == 2
    assert docker_evidence.questions_asked[0].record_id == "q1"
    assert docker_evidence.resume_evidence == "partial"
    assert docker_evidence.candidate_claim == "Used Docker in a side project"
    assert docker_evidence.interview_evidence == "strong"
    assert docker_evidence.final_assessment == "strong"
    assert docker_evidence.followup_depth == 1
    assert docker_evidence.followup_categories_used == ["followup_depth"]
    assert docker_evidence.skip_reason is None

    rust_evidence = next(t for t in validated.topic_evidence if t.topic_id == "rust")
    assert rust_evidence.questions_asked == []
    assert rust_evidence.skip_reason == "deprioritized"

    # requirement_coverage
    assert validated.requirement_coverage.total_topics == 2
    assert validated.requirement_coverage.total_never_reached == 1
    assert validated.requirement_coverage.by_criticality["critical"].verified == 1
    assert validated.requirement_coverage.by_criticality["resume_only"].never_reached == 1


@pytest.mark.asyncio
async def test_in_progress_shape_validates_with_most_fields_absent():
    """The early-return (non-COMPLETED) shape must also validate — proving
    the optionality is honest, not just permissive."""
    svc = InterviewResultService.__new__(InterviewResultService)
    session = _make_session(
        question_history=[], evaluation_history=[], topic_progress=[],
        blueprint_topics=[],
    )
    session.state = InterviewState.IN_PROGRESS
    mock_repo = MagicMock()
    mock_repo.get_by_id = AsyncMock(return_value=session)
    svc._engine_repo = mock_repo

    report = await svc.generate_result_report("s1")
    validated = ReportResponse.model_validate(report)

    assert validated.status == "IN_PROGRESS"
    assert validated.has_report is False
    assert validated.message == "Interview is not yet completed."
    assert validated.topic_scores is None
    assert validated.topic_evidence is None
    assert validated.requirement_coverage is None
    assert validated.overall_score is None


def test_stale_mock_fields_are_no_longer_part_of_the_schema():
    """A test that would fail if the old stale fields were still required
    (or even still present as declared fields) on ReportResponse."""
    stale_fields = {
        "technical_score", "communication_score", "confidence", "problem_solving",
        "soft_skills_score", "time_management", "resume_match", "radar_data",
    }
    declared_fields = set(ReportResponse.model_fields.keys())
    assert not (stale_fields & declared_fields), (
        f"Stale mock-era fields still declared on ReportResponse: {stale_fields & declared_fields}"
    )


def test_minimal_valid_report_response_requires_only_the_three_always_present_fields():
    """session_id, status, has_report are the only fields the service
    guarantees on every call — everything else must be optional."""
    minimal = ReportResponse(session_id="s1", status="COMPLETED_NO_DATA", has_report=False)
    assert minimal.topic_scores is None
    assert minimal.topic_evidence is None

    with pytest.raises(ValidationError):
        ReportResponse(status="COMPLETED_NO_DATA", has_report=False)  # missing session_id


def test_final_assessment_rejects_values_outside_the_five_value_vocabulary():
    from app.schemas.candidate_portal import TopicEvidence
    with pytest.raises(ValidationError):
        TopicEvidence(
            topic_id="t", topic_name="T", final_assessment="excellent",  # not a valid literal
            followup_depth=0,
        )
