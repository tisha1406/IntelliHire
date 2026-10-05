"""
tests/api/test_interview_report_endpoint.py
===========================================
API-layer tests for GET /api/interview/sessions/{session_id}/report.
"""

import uuid
import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient

from app.auth.jwt_handler import create_access_token
from app.rbac.models import UserRole
from app.ai_interview.transport.schemas.ws_events import SessionSnapshotData

from app.main import app
from app.api.interview import get_transport_service, get_result_service
from app.schemas.candidate_portal import ReportResponse

CANDIDATE_ID = "cand-test-001"
OTHER_CANDIDATE_ID = "cand-test-002"
SESSION_ID = "session-abc-001"

BANNED_FIELDS = [
    "communication_score", "confidence", "problem_solving",
    "soft_skills_score", "time_management", "resume_match",
    "radar_data", "technical_score",
]

def _auth_header(candidate_id: str = CANDIDATE_ID) -> dict:
    t = create_access_token("user-001", UserRole.CANDIDATE.value, candidate_id=candidate_id)
    return {"Authorization": f"Bearer {t}"}

def _make_completed_snapshot() -> SessionSnapshotData:
    return SessionSnapshotData(
        session_id=SESSION_ID, interview_state="completed", questions_asked_total=3,
        total_question_budget=6, min_questions=2, is_paused=False,
        is_completed=True, is_failed=False, waiting_for_answer=False,
    )

def _make_inprogress_snapshot() -> SessionSnapshotData:
    return SessionSnapshotData(
        session_id=SESSION_ID, interview_state="in_progress", questions_asked_total=1,
        total_question_budget=6, min_questions=2, current_topic_id="py",
        is_paused=False, is_completed=False, is_failed=False, waiting_for_answer=True,
    )

def _completed_report_with_score(overall_score: int = 75) -> dict:
    return {
        "session_id": SESSION_ID, "status": "COMPLETED", "has_report": True,
        "overall_score": overall_score, "question_count": 3,
        "completed_at": "2026-09-16T17:00:00+00:00",
        "question_feedback": [
            {"id": "1", "question_record_id": "qr1", "topic_id": "py", "topic": "Python",
             "question": "Q", "difficulty": "medium", "question_type": "initial",
             "score": 0.75, "score_100": 75, "coverage_signal": "qualitatively_covered",
             "follow_up_signal": "none", "evaluated_at": "2026-09-16T17:00:00+00:00"}
        ],
        "topic_scores": [
            {"topic_id": "py", "topic_name": "Python", "questions_asked": 3,
             "answers_evaluated": 3, "average_score": 0.75, "score_100": 75,
             "strong_answers": 1, "partial_answers": 2, "weak_answers": 0,
             "insufficient_answers": 0, "qualitatively_covered": True, "coverage_score": 0.75}
        ],
        "strengths": ["Good"], "weaknesses": ["None"],
        "improvement_suggestions": ["Keep going"], "company_remarks": "OK"
    }

def _no_evaluations_report() -> dict:
    return {"session_id": SESSION_ID, "status": "COMPLETED_NO_DATA", "has_report": False, "message": "No data"}

def _inprogress_report() -> dict:
    return {"session_id": SESSION_ID, "status": "IN_PROGRESS", "has_report": False, "message": "In progress"}

URL = f"/api/interview/sessions/{SESSION_ID}/report"

def test_01_completed_session_returns_200_with_real_report():
    mock_transport = MagicMock()
    mock_transport.get_session_snapshot = AsyncMock(return_value=_make_completed_snapshot())
    mock_result = MagicMock()
    mock_result.generate_result_report = AsyncMock(return_value=_completed_report_with_score(75))
    
    app.dependency_overrides[get_transport_service] = lambda: mock_transport
    app.dependency_overrides[get_result_service] = lambda: mock_result
    try:
        client = TestClient(app)
        resp = client.get(URL, headers=_auth_header())
    finally:
        app.dependency_overrides.clear()
        
    assert resp.status_code == 200, resp.text
    assert resp.json()["overall_score"] == 75
    assert resp.json()["has_report"] is True


def test_02_overall_score_from_real_evaluations():
    mock_transport = MagicMock()
    mock_transport.get_session_snapshot = AsyncMock(return_value=_make_completed_snapshot())
    mock_result = MagicMock()
    mock_result.generate_result_report = AsyncMock(return_value=_completed_report_with_score(67))
    
    app.dependency_overrides[get_transport_service] = lambda: mock_transport
    app.dependency_overrides[get_result_service] = lambda: mock_result
    try:
        client = TestClient(app)
        resp = client.get(URL, headers=_auth_header())
    finally:
        app.dependency_overrides.clear()
        
    assert resp.status_code == 200, resp.text
    assert resp.json()["overall_score"] == 67
    for k in BANNED_FIELDS: assert k not in resp.json()


def test_03_inprogress_session_returns_200_no_report():
    mock_transport = MagicMock()
    mock_transport.get_session_snapshot = AsyncMock(return_value=_make_inprogress_snapshot())
    mock_result = MagicMock()
    mock_result.generate_result_report = AsyncMock(return_value=_inprogress_report())
    
    app.dependency_overrides[get_transport_service] = lambda: mock_transport
    app.dependency_overrides[get_result_service] = lambda: mock_result
    try:
        client = TestClient(app)
        resp = client.get(URL, headers=_auth_header())
    finally:
        app.dependency_overrides.clear()
        
    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "IN_PROGRESS"
    assert resp.json()["has_report"] is False


def test_04_nonexistent_session_returns_404():
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


def test_05_wrong_candidate_returns_403():
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


def test_06_completed_no_evaluations_returns_safe_state():
    mock_transport = MagicMock()
    mock_transport.get_session_snapshot = AsyncMock(return_value=_make_completed_snapshot())
    mock_result = MagicMock()
    mock_result.generate_result_report = AsyncMock(return_value=_no_evaluations_report())
    
    app.dependency_overrides[get_transport_service] = lambda: mock_transport
    app.dependency_overrides[get_result_service] = lambda: mock_result
    try:
        client = TestClient(app)
        resp = client.get(URL, headers=_auth_header())
    finally:
        app.dependency_overrides.clear()
        
    assert resp.status_code == 200, resp.text
    assert resp.json()["has_report"] is False
    assert resp.json()["status"] == "COMPLETED_NO_DATA"


def test_07_no_hardcoded_mock_score_fields_in_response():
    mock_transport = MagicMock()
    mock_transport.get_session_snapshot = AsyncMock(return_value=_make_completed_snapshot())
    mock_result = MagicMock()
    mock_result.generate_result_report = AsyncMock(return_value=_completed_report_with_score(82))
    
    app.dependency_overrides[get_transport_service] = lambda: mock_transport
    app.dependency_overrides[get_result_service] = lambda: mock_result
    try:
        client = TestClient(app)
        resp = client.get(URL, headers=_auth_header())
    finally:
        app.dependency_overrides.clear()
        
    assert resp.status_code == 200
    for k in BANNED_FIELDS: assert k not in resp.json()


def test_09_d01_evidence_fields_pass_through_the_endpoint_unfiltered():
    """D-01 regression: GET /sessions/{id}/report has no response_model
    attached (confirmed by reading app/api/interview.py), so whatever
    InterviewResultService.generate_result_report() returns passes straight
    through. This proves the new evidence-model fields reach the actual HTTP
    response and are not silently stripped.

    Per the D-01 correction: topic_scores[].questions_asked stays an
    unmodified int; the evidence fields (including questions_asked as a list)
    live in a separate sibling "topic_evidence" list.
    """
    report = _completed_report_with_score(75)
    assert report["topic_scores"][0]["questions_asked"] == 3  # unchanged int, untouched by this test
    report["topic_evidence"] = [{
        "topic_id": "py",
        "topic_name": "Python",
        "resume_evidence": "partial",
        "candidate_claim": "I used Docker in a side project",
        "interview_evidence": "strong",
        "final_assessment": "strong",
        "questions_asked": [{"record_id": "qr1", "question_text": "Q"}],
        "followup_depth": 1,
        "followup_categories_used": ["followup_depth"],
        "skip_reason": None,
    }]
    report["requirement_coverage"] = {
        "by_criticality": {"critical": {"total": 1, "verified": 1, "not_verified": 0, "never_reached": 0}},
        "total_topics": 1, "total_verified": 1, "total_not_verified": 0, "total_never_reached": 0,
    }

    mock_transport = MagicMock()
    mock_transport.get_session_snapshot = AsyncMock(return_value=_make_completed_snapshot())
    mock_result = MagicMock()
    mock_result.generate_result_report = AsyncMock(return_value=report)

    app.dependency_overrides[get_transport_service] = lambda: mock_transport
    app.dependency_overrides[get_result_service] = lambda: mock_result
    try:
        client = TestClient(app)
        resp = client.get(URL, headers=_auth_header())
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["requirement_coverage"]["total_verified"] == 1

    # topic_scores is untouched: "questions_asked" is still the int count.
    assert body["topic_scores"][0]["questions_asked"] == 3
    assert isinstance(body["topic_scores"][0]["questions_asked"], int)

    # topic_evidence carries the D-01 fields, with "questions_asked" as a list.
    topic = body["topic_evidence"][0]
    assert topic["resume_evidence"] == "partial"
    assert topic["candidate_claim"] == "I used Docker in a side project"
    assert topic["interview_evidence"] == "strong"
    assert topic["final_assessment"] == "strong"
    assert isinstance(topic["questions_asked"], list)
    assert topic["questions_asked"][0]["record_id"] == "qr1"
    assert topic["followup_depth"] == 1
    assert topic["followup_categories_used"] == ["followup_depth"]
    # Existing fields still present alongside the new ones.
    assert body["overall_score"] == 75


def test_08_no_candidate_id_in_token_returns_403():
    bad_token = create_access_token("user-001", UserRole.CANDIDATE.value, candidate_id=None)
    mock_transport = MagicMock()
    mock_result = MagicMock()
    
    app.dependency_overrides[get_transport_service] = lambda: mock_transport
    app.dependency_overrides[get_result_service] = lambda: mock_result
    try:
        client = TestClient(app)
        resp = client.get(URL, headers={"Authorization": f"Bearer {bad_token}"})
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 403, resp.text


def test_10_d02_live_endpoint_response_validates_against_report_response():
    """D-02 endpoint-level regression: the actual HTTP JSON body returned by
    this route must validate against ReportResponse, not just a hand-built
    dict fed directly to the schema."""
    report = _completed_report_with_score(75)
    report["topic_evidence"] = [{
        "topic_id": "py",
        "topic_name": "Python",
        "resume_evidence": "partial",
        "candidate_claim": "I used Docker in a side project",
        "interview_evidence": "strong",
        "final_assessment": "strong",
        "questions_asked": [{
            "record_id": "qr1", "question_text": "Q", "question_type": "initial",
            "difficulty": "medium", "category": None, "turn_number": 1, "asked_at": None,
        }],
        "followup_depth": 1,
        "followup_categories_used": ["followup_depth"],
        "skip_reason": None,
    }]
    report["requirement_coverage"] = {
        "by_criticality": {
            "critical": {"total": 1, "verified": 1, "not_verified": 0, "never_reached": 0},
        },
        "total_topics": 1, "total_verified": 1, "total_not_verified": 0, "total_never_reached": 0,
    }

    mock_transport = MagicMock()
    mock_transport.get_session_snapshot = AsyncMock(return_value=_make_completed_snapshot())
    mock_result = MagicMock()
    mock_result.generate_result_report = AsyncMock(return_value=report)

    app.dependency_overrides[get_transport_service] = lambda: mock_transport
    app.dependency_overrides[get_result_service] = lambda: mock_result
    try:
        client = TestClient(app)
        resp = client.get(URL, headers=_auth_header())
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 200, resp.text
    validated = ReportResponse.model_validate(resp.json())  # must not raise
    assert validated.topic_scores[0].questions_asked == 3
    assert isinstance(validated.topic_scores[0].questions_asked, int)
    assert validated.topic_evidence[0].questions_asked[0].record_id == "qr1"
