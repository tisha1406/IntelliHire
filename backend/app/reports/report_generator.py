"""
D-05: orchestration layer between InterviewResultService and pdf_renderer.

Deliberately thin -- this module does NOT recompute or re-derive any scoring,
evidence, or requirement-coverage logic. It only fetches the already-built
report dict from InterviewResultService (the single source of truth for
report data, unchanged by D-05) and hands it to pdf_renderer for layout.
"""
from typing import Any

from app.reports.pdf_renderer import render_interview_report_pdf


async def generate_report_pdf(session_id: str, result_service: Any) -> bytes:
    """
    Fetches the real interview report for session_id via the given
    InterviewResultService instance and renders it to PDF bytes.

    Callers are responsible for session ownership/auth checks before calling
    this (see app/api/interview.py's get_report_pdf and
    app/api/company/candidates.py's get_interview_results_pdf, which mirror
    the existing JSON endpoints' own ownership checks exactly).
    """
    report = await result_service.generate_result_report(session_id)
    return render_interview_report_pdf(report)
