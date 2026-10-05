"""
D-05 tests for the company-side PDF endpoint:
GET /company/candidates/interviews/{session_id}/results/pdf

Mirrors C-01's own testing convention (test_company_candidate_lifecycle_actions.py):
route functions called directly as plain coroutines with repository classes
patched, rather than spinning up a full authenticated HTTP client -- this
endpoint reuses the exact same ownership check as the pre-existing
get_interview_results() JSON endpoint (ObjectId'd company_id string
comparison against session["company_id"]), which had no dedicated test
coverage of its own before D-05.
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import HTTPException
from bson import ObjectId

from app.auth.jwt_handler import TokenPayload
from app.api.company.candidates import get_interview_results_pdf
from pypdf import PdfReader
from io import BytesIO

SESSION_ID = "session-xyz-001"


def _company_token(company_id: str) -> TokenPayload:
    return TokenPayload(sub=company_id, role="company", exp=9999999999, iat=0)


def _recruiter_token(company_id: str, recruiter_id: str) -> TokenPayload:
    return TokenPayload(
        sub=company_id, role="recruiter", company_id=company_id,
        recruiter_id=recruiter_id, exp=9999999999, iat=0,
    )


def _completed_report(overall_score: int = 80) -> dict:
    return {
        "session_id": SESSION_ID, "status": "COMPLETED", "has_report": True,
        "overall_score": overall_score, "question_count": 2, "completed_at": "2026-01-01T00:00:00+00:00",
        "question_feedback": [], "topic_scores": [], "strengths": ["Good"],
        "weaknesses": ["None"], "improvement_suggestions": ["Keep going"],
        "company_remarks": "AI Evaluation Completed.",
        "requirement_coverage": None, "topic_evidence": None,
    }


class TestCompanyPdfOwnership:
    @pytest.mark.asyncio
    async def test_company_can_download_its_own_session_report_pdf(self):
        session = {"_id": ObjectId(), "company_id": "company_1"}
        with patch("app.api.company.candidates.InterviewSessionRepository") as MockRepo, \
             patch("app.services.interview_result_service.InterviewResultService") as MockService:
            MockRepo.return_value.get_by_session_id = AsyncMock(return_value=session)
            MockService.return_value.generate_result_report = AsyncMock(
                return_value=_completed_report(80)
            )

            resp = await get_interview_results_pdf(SESSION_ID, _company_token("company_1"))

        assert resp.media_type == "application/pdf"
        assert resp.body.startswith(b"%PDF-")
        reader = PdfReader(BytesIO(resp.body))
        assert len(reader.pages) >= 1

    @pytest.mark.asyncio
    async def test_recruiter_can_download_their_companys_session_report_pdf(self):
        session = {"_id": ObjectId(), "company_id": "company_1"}
        with patch("app.api.company.candidates.InterviewSessionRepository") as MockRepo, \
             patch("app.services.interview_result_service.InterviewResultService") as MockService:
            MockRepo.return_value.get_by_session_id = AsyncMock(return_value=session)
            MockService.return_value.generate_result_report = AsyncMock(
                return_value=_completed_report(80)
            )

            resp = await get_interview_results_pdf(
                SESSION_ID, _recruiter_token("company_1", "recruiter_1")
            )

        assert resp.media_type == "application/pdf"

    @pytest.mark.asyncio
    async def test_cross_tenant_session_is_forbidden(self):
        session = {"_id": ObjectId(), "company_id": "company_2"}
        with patch("app.api.company.candidates.InterviewSessionRepository") as MockRepo:
            MockRepo.return_value.get_by_session_id = AsyncMock(return_value=session)

            with pytest.raises(HTTPException) as exc_info:
                await get_interview_results_pdf(SESSION_ID, _company_token("company_1"))

        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_nonexistent_session_returns_404(self):
        with patch("app.api.company.candidates.InterviewSessionRepository") as MockRepo:
            MockRepo.return_value.get_by_session_id = AsyncMock(return_value=None)

            with pytest.raises(HTTPException) as exc_info:
                await get_interview_results_pdf(SESSION_ID, _company_token("company_1"))

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_report_data_appears_in_the_pdf(self):
        session = {"_id": ObjectId(), "company_id": "company_1"}
        with patch("app.api.company.candidates.InterviewSessionRepository") as MockRepo, \
             patch("app.services.interview_result_service.InterviewResultService") as MockService:
            MockRepo.return_value.get_by_session_id = AsyncMock(return_value=session)
            MockService.return_value.generate_result_report = AsyncMock(
                return_value=_completed_report(93)
            )

            resp = await get_interview_results_pdf(SESSION_ID, _company_token("company_1"))

        reader = PdfReader(BytesIO(resp.body))
        text = "\n".join(p.extract_text() or "" for p in reader.pages)
        assert "93" in text
        assert "AI Evaluation Completed." in text
