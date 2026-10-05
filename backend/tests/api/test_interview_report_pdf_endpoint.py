"""
D-05 tests: GET /api/interview/sessions/{session_id}/report/pdf.

Mirrors test_interview_report_endpoint.py's exact mocking convention (same
dependency overrides, same fixtures) -- the PDF endpoint reuses the identical
ownership check and InterviewResultService call as the JSON endpoint, so the
only new behavior to prove is: a real PDF comes back, with the correct media
type, built from the same report data, and no LLM/database call happens
inside the PDF-rendering path itself.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock

from fastapi.testclient import TestClient
from pypdf import PdfReader
from io import BytesIO

from app.auth.jwt_handler import create_access_token
from app.rbac.models import UserRole
from app.ai_interview.transport.schemas.ws_events import SessionSnapshotData

from app.main import app
from app.api.interview import get_transport_service, get_result_service

CANDIDATE_ID = "cand-test-001"
OTHER_CANDIDATE_ID = "cand-test-002"
SESSION_ID = "session-abc-001"

URL = f"/api/interview/sessions/{SESSION_ID}/report/pdf"


def _auth_header(candidate_id: str = CANDIDATE_ID) -> dict:
    t = create_access_token("user-001", UserRole.CANDIDATE.value, candidate_id=candidate_id)
    return {"Authorization": f"Bearer {t}"}


def _make_completed_snapshot() -> SessionSnapshotData:
    return SessionSnapshotData(
        session_id=SESSION_ID, interview_state="completed", questions_asked_total=3,
        total_question_budget=6, min_questions=2, is_paused=False,
        is_completed=True, is_failed=False, waiting_for_answer=False,
    )


def _completed_report_with_score(overall_score: int = 75) -> dict:
    return {
        "session_id": SESSION_ID, "status": "COMPLETED", "has_report": True,
        "overall_score": overall_score, "question_count": 3,
        "completed_at": "2026-09-16T17:00:00+00:00",
        "question_feedback": [
            {"id": "1", "question_record_id": "qr1", "topic_id": "py", "topic": "Python",
             "question": "Explain the GIL and how it affects multithreaded Python programs.",
             "difficulty": "medium", "question_type": "initial",
             "score": 0.75, "score_100": 75, "coverage_signal": "qualitatively_covered",
             "follow_up_signal": "none", "evaluated_at": "2026-09-16T17:00:00+00:00"}
        ],
        "topic_scores": [
            {"topic_id": "py", "topic_name": "Python", "questions_asked": 3,
             "answers_evaluated": 3, "average_score": 0.75, "score_100": 75,
             "strong_answers": 1, "partial_answers": 2, "weak_answers": 0,
             "insufficient_answers": 0, "qualitatively_covered": True, "coverage_score": 0.75}
        ],
        "strengths": ["Good grasp of Python internals"],
        "weaknesses": ["Limited depth on concurrency"],
        "improvement_suggestions": ["Practice explaining the GIL with examples"],
        "company_remarks": "AI Evaluation Completed.",
        "requirement_coverage": {
            "by_criticality": {
                "critical": {"total": 1, "verified": 1, "not_verified": 0, "never_reached": 0},
            },
            "total_topics": 1, "total_verified": 1, "total_not_verified": 0, "total_never_reached": 0,
        },
        "topic_evidence": [
            {"topic_id": "py", "topic_name": "Python", "questions_asked": [],
             "resume_evidence": "strong", "candidate_claim": "Used Python for 3 years",
             "interview_evidence": "strong", "final_assessment": "strong",
             "followup_depth": 1, "followup_categories_used": ["followup_depth"],
             "skip_reason": None},
        ],
    }


def _inprogress_report() -> dict:
    return {"session_id": SESSION_ID, "status": "IN_PROGRESS", "has_report": False, "message": "In progress"}


def _extract_text(pdf_bytes: bytes) -> str:
    reader = PdfReader(BytesIO(pdf_bytes))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def _get_pdf(report: dict, snapshot=None):
    mock_transport = MagicMock()
    mock_transport.get_session_snapshot = AsyncMock(return_value=snapshot or _make_completed_snapshot())
    mock_result = MagicMock()
    mock_result.generate_result_report = AsyncMock(return_value=report)

    app.dependency_overrides[get_transport_service] = lambda: mock_transport
    app.dependency_overrides[get_result_service] = lambda: mock_result
    try:
        client = TestClient(app)
        resp = client.get(URL, headers=_auth_header())
    finally:
        app.dependency_overrides.clear()
    return resp


# ── A/B. A completed report produces a real, correctly-typed PDF ───────────

def test_completed_report_returns_real_pdf_with_correct_media_type():
    resp = _get_pdf(_completed_report_with_score(75))

    assert resp.status_code == 200, resp.text
    assert resp.headers["content-type"] == "application/pdf"
    assert resp.content.startswith(b"%PDF-")


def test_returned_content_is_a_structurally_valid_pdf():
    """Prefer structural validation (a real parser can open it, get a page
    count, extract text) over brittle byte-for-byte comparison."""
    resp = _get_pdf(_completed_report_with_score(75))
    reader = PdfReader(BytesIO(resp.content))
    assert len(reader.pages) >= 1


# ── D. Current report data appears in the generated document ───────────────

def test_current_report_data_appears_in_the_document():
    resp = _get_pdf(_completed_report_with_score(88))
    text = _extract_text(resp.content)

    assert "88" in text  # overall_score
    assert "Python" in text  # topic_name
    assert "Good grasp of Python internals" in text  # strengths
    assert "Limited depth on concurrency" in text  # weaknesses
    assert "AI Evaluation Completed." in text  # company_remarks
    assert SESSION_ID in text


# ── E/F. Missing optional fields / early-return shape don't break generation ─

def test_in_progress_report_still_produces_a_valid_pdf_not_an_error():
    resp = _get_pdf(_inprogress_report())

    assert resp.status_code == 200, resp.text
    assert resp.content.startswith(b"%PDF-")
    reader = PdfReader(BytesIO(resp.content))
    assert len(reader.pages) >= 1


def test_missing_optional_fields_do_not_break_generation():
    minimal = {
        "session_id": SESSION_ID, "status": "COMPLETED", "has_report": True,
        "overall_score": 60, "question_count": 1, "completed_at": None,
        "question_feedback": [], "topic_scores": [],
        "strengths": [], "weaknesses": [], "improvement_suggestions": [],
        "company_remarks": None,
        "requirement_coverage": None,
        "topic_evidence": None,
    }
    resp = _get_pdf(minimal)
    assert resp.status_code == 200, resp.text
    assert resp.content.startswith(b"%PDF-")


def test_topic_evidence_and_requirement_coverage_render_without_breaking():
    report = _completed_report_with_score(70)
    resp = _get_pdf(report)
    text = _extract_text(resp.content)

    assert "strong" in text.lower()  # final_assessment / resume_evidence / interview_evidence
    assert "critical" in text.lower()  # requirement_coverage criticality bucket


# ── G. No LLM call, no scenario lookup, DB only via the mocked services ─────

def test_endpoint_source_makes_no_llm_or_scenario_calls():
    import inspect
    from app.api import interview as interview_module

    source = inspect.getsource(interview_module.get_report_pdf)
    assert "LLM" not in source
    assert "llm" not in source.lower()
    assert "ScenarioRepository" not in source
    assert "scenario_repository" not in source


# ── H. Auth/ownership behavior matches the existing JSON endpoint exactly ──

def test_nonexistent_session_returns_404():
    mock_transport = MagicMock()
    mock_transport.get_session_snapshot = AsyncMock(side_effect=ValueError("Session not found"))
    mock_result = MagicMock()

    app.dependency_overrides[get_transport_service] = lambda: mock_transport
    app.dependency_overrides[get_result_service] = lambda: mock_result
    try:
        client = TestClient(app)
        resp = client.get(URL, headers=_auth_header())
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 404, resp.text


def test_wrong_candidate_returns_403():
    mock_transport = MagicMock()
    mock_transport.get_session_snapshot = AsyncMock(side_effect=ValueError("Forbidden"))
    mock_result = MagicMock()

    app.dependency_overrides[get_transport_service] = lambda: mock_transport
    app.dependency_overrides[get_result_service] = lambda: mock_result
    try:
        client = TestClient(app)
        resp = client.get(URL, headers=_auth_header(OTHER_CANDIDATE_ID))
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 403, resp.text


# ── I. Existing JSON report endpoint is unaffected ──────────────────────────

def test_existing_json_report_endpoint_still_works_unchanged():
    json_url = f"/api/interview/sessions/{SESSION_ID}/report"
    mock_transport = MagicMock()
    mock_transport.get_session_snapshot = AsyncMock(return_value=_make_completed_snapshot())
    mock_result = MagicMock()
    mock_result.generate_result_report = AsyncMock(return_value=_completed_report_with_score(75))

    app.dependency_overrides[get_transport_service] = lambda: mock_transport
    app.dependency_overrides[get_result_service] = lambda: mock_result
    try:
        client = TestClient(app)
        resp = client.get(json_url, headers=_auth_header())
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 200, resp.text
    assert resp.headers["content-type"].startswith("application/json")
    assert resp.json()["overall_score"] == 75
