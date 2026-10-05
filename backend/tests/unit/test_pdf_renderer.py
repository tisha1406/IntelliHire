"""
D-05 unit tests for app.reports.pdf_renderer / report_generator.

Pure-function tests, no HTTP layer, no mocked FastAPI dependencies -- proves
render_interview_report_pdf() itself produces valid, data-reflecting PDFs and
tolerates the full range of shapes InterviewResultService.generate_result_report()
can actually return, without touching scoring/evidence/requirement-coverage logic.
"""
from io import BytesIO

import pytest
from pypdf import PdfReader
from unittest.mock import AsyncMock, MagicMock

from app.reports.pdf_renderer import render_interview_report_pdf
from app.reports.report_generator import generate_report_pdf


def _extract_text(pdf_bytes: bytes) -> str:
    reader = PdfReader(BytesIO(pdf_bytes))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def _full_report(**overrides) -> dict:
    base = {
        "session_id": "s1", "status": "COMPLETED", "has_report": True,
        "overall_score": 82, "question_count": 2, "completed_at": "2026-01-01T00:00:00+00:00",
        "question_feedback": [
            {"id": "1", "question_record_id": "q1", "topic_id": "docker", "topic": "Docker",
             "question": "How would you reduce a Docker image size?", "difficulty": "medium",
             "question_type": "initial", "score": 0.85, "score_100": 85,
             "coverage_signal": "qualitatively_covered", "follow_up_signal": "none",
             "evaluated_at": "2026-01-01T00:00:00+00:00"},
        ],
        "topic_scores": [
            {"topic_id": "docker", "topic_name": "Docker", "questions_asked": 2,
             "answers_evaluated": 2, "average_score": 0.85, "score_100": 85,
             "strong_answers": 2, "partial_answers": 0, "weak_answers": 0,
             "insufficient_answers": 0, "qualitatively_covered": True, "coverage_score": 0.85},
        ],
        "strengths": ["Strong grasp of Docker fundamentals"],
        "weaknesses": ["Limited depth on networking"],
        "improvement_suggestions": ["Practice explaining tradeoffs explicitly"],
        "company_remarks": "AI Evaluation Completed.",
        "requirement_coverage": {
            "by_criticality": {"critical": {"total": 1, "verified": 1, "not_verified": 0, "never_reached": 0}},
            "total_topics": 1, "total_verified": 1, "total_not_verified": 0, "total_never_reached": 0,
        },
        "topic_evidence": [
            {"topic_id": "docker", "topic_name": "Docker", "questions_asked": [],
             "resume_evidence": "partial", "candidate_claim": "Used Docker in a side project",
             "interview_evidence": "strong", "final_assessment": "strong",
             "followup_depth": 1, "followup_categories_used": ["followup_depth"], "skip_reason": None},
        ],
    }
    base.update(overrides)
    return base


class TestRealCompletedReport:
    def test_produces_a_valid_openable_pdf(self):
        pdf_bytes = render_interview_report_pdf(_full_report())
        assert pdf_bytes.startswith(b"%PDF-")
        reader = PdfReader(BytesIO(pdf_bytes))
        assert len(reader.pages) >= 1

    def test_report_data_appears_in_the_document(self):
        pdf_bytes = render_interview_report_pdf(_full_report(overall_score=91))
        text = _extract_text(pdf_bytes)
        assert "91" in text
        assert "Docker" in text
        assert "Strong grasp of Docker fundamentals" in text
        assert "Limited depth on networking" in text
        assert "Practice explaining tradeoffs explicitly" in text
        assert "AI Evaluation Completed." in text

    def test_does_not_expose_internal_record_ids(self):
        """Internal Mongo/record identifiers (question_record_id, topic_id)
        are not meaningful to a human reading the PDF and should not appear
        unnecessarily -- only human-readable labels (topic_name, question
        text) should."""
        pdf_bytes = render_interview_report_pdf(_full_report())
        text = _extract_text(pdf_bytes)
        assert "q1" not in text
        assert "docker" not in text  # the topic_id (lowercase); "Docker" (topic_name) is fine


class TestMissingOptionalFields:
    def test_no_topic_evidence_or_requirement_coverage(self):
        report = _full_report(topic_evidence=None, requirement_coverage=None)
        pdf_bytes = render_interview_report_pdf(report)
        assert pdf_bytes.startswith(b"%PDF-")

    def test_no_question_feedback_or_topic_scores(self):
        report = _full_report(question_feedback=[], topic_scores=[])
        pdf_bytes = render_interview_report_pdf(report)
        assert pdf_bytes.startswith(b"%PDF-")

    def test_no_company_remarks(self):
        report = _full_report(company_remarks=None)
        pdf_bytes = render_interview_report_pdf(report)
        assert pdf_bytes.startswith(b"%PDF-")

    def test_empty_strengths_weaknesses_improvement_suggestions(self):
        report = _full_report(strengths=[], weaknesses=[], improvement_suggestions=[])
        pdf_bytes = render_interview_report_pdf(report)
        text = _extract_text(pdf_bytes)
        assert pdf_bytes.startswith(b"%PDF-")
        assert "None recorded." in text


class TestNonCompletedShapes:
    def test_in_progress_shape_produces_pending_pdf(self):
        report = {"session_id": "s1", "status": "IN_PROGRESS", "has_report": False, "message": "Not done yet."}
        pdf_bytes = render_interview_report_pdf(report)
        assert pdf_bytes.startswith(b"%PDF-")
        text = _extract_text(pdf_bytes)
        assert "Not done yet." in text

    def test_completed_no_data_shape_produces_pending_pdf(self):
        report = {"session_id": "s1", "status": "COMPLETED_NO_DATA", "has_report": False, "message": "No evaluations."}
        pdf_bytes = render_interview_report_pdf(report)
        assert pdf_bytes.startswith(b"%PDF-")
        text = _extract_text(pdf_bytes)
        assert "No evaluations." in text


class TestReportGeneratorOrchestration:
    @pytest.mark.asyncio
    async def test_fetches_via_the_given_result_service_and_renders(self):
        """Proves generate_report_pdf() does not recompute report data itself
        -- it delegates entirely to the injected result_service."""
        mock_service = MagicMock()
        mock_service.generate_result_report = AsyncMock(return_value=_full_report(overall_score=77))

        pdf_bytes = await generate_report_pdf("s1", mock_service)

        mock_service.generate_result_report.assert_awaited_once_with("s1")
        assert pdf_bytes.startswith(b"%PDF-")
        text = _extract_text(pdf_bytes)
        assert "77" in text
