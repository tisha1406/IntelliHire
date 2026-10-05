"""
D-05: real PDF rendering for the candidate/company interview report.

Pure function: the report dict produced by
app.services.interview_result_service.InterviewResultService
.generate_result_report() -> PDF bytes. No DB access, no LLM call, no
scenario lookup, no scoring logic -- this module only ever reads an
already-computed report dict and lays it out as a document.

Uses reportlab (pure Python, no native system-library dependencies) rather
than the originally-planned WeasyPrint/Jinja2 HTML pipeline. specs.md's own
risk note (§33) flagged WeasyPrint's native Pango/Cairo/GDK-Pixbuf dependency
chain as "a known source of clean-install friction, especially on Windows,
and ... likely *why* PDF generation was never finished" -- this was confirmed
directly during the D-05 audit: `import weasyprint` fails on this Windows
dev environment with an OSError loading libgobject-2.0-0, even though the
package is pip-installed. reportlab has no such dependency and was already
present in this environment.
"""
from datetime import datetime, timezone
from io import BytesIO
from typing import Any, Dict, List, Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    ListFlowable,
    ListItem,
)

_styles = getSampleStyleSheet()
_TITLE = ParagraphStyle("D05Title", parent=_styles["Title"], fontSize=18, spaceAfter=4)
_H2 = ParagraphStyle("D05H2", parent=_styles["Heading2"], spaceBefore=14, spaceAfter=6)
_BODY = _styles["BodyText"]
_MUTED = ParagraphStyle("D05Muted", parent=_styles["BodyText"], textColor=colors.grey, fontSize=9)

_CELL = ParagraphStyle("D05Cell", parent=_styles["BodyText"], fontSize=9, leading=11)


def _cell(text: Any) -> Paragraph:
    """Wraps table-cell text in a Paragraph so long strings (question text,
    long topic names) wrap within the column instead of overflowing it."""
    return Paragraph(str(text) if text not in (None, "") else "—", _CELL)


_TABLE_HEADER_STYLE = TableStyle([
    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1D4ED8")),
    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
    ("FONTSIZE", (0, 0), (-1, -1), 9),
    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
    ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
])


def _p(text: Any, style=_BODY) -> Paragraph:
    """Safely wraps a value as a Paragraph, escaping nothing-to-worry-about
    plain text and tolerating None/missing values."""
    return Paragraph(str(text) if text not in (None, "") else "—", style)


def _bullet_list(items: Optional[List[str]]) -> ListFlowable:
    items = items or []
    if not items:
        return ListFlowable([ListItem(_p("None recorded."))], bulletType="bullet")
    return ListFlowable([ListItem(_p(item)) for item in items], bulletType="bullet")


def _pending_report_pdf(report: Dict[str, Any]) -> bytes:
    """Report not yet available (IN_PROGRESS / COMPLETED_NO_DATA) -- still a
    real, valid, openable PDF rather than a crash or an empty file."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=2 * cm, bottomMargin=2 * cm)
    story = [
        Paragraph("IntelliHire Interview Report", _TITLE),
        Spacer(1, 0.3 * cm),
        _p(f"Session: {report.get('session_id', 'Unknown')}", _MUTED),
        Spacer(1, 1 * cm),
        Paragraph("Report Not Yet Available", _H2),
        _p(report.get("message") or "This interview report is not yet available."),
    ]
    doc.build(story)
    return buffer.getvalue()


def render_interview_report_pdf(report: Dict[str, Any]) -> bytes:
    """
    Builds a real, valid PDF document from an interview report dict.

    Handles both report shapes generate_result_report() can return:
      - not report.get("has_report"): a short "pending" document.
      - has_report=True: the full evidence-aware report.

    Every section tolerates missing/None fields -- this function never
    assumes a key is present beyond what ReportResponse already declares as
    optional.
    """
    if not report.get("has_report"):
        return _pending_report_pdf(report)

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4, topMargin=1.8 * cm, bottomMargin=1.8 * cm,
        leftMargin=1.8 * cm, rightMargin=1.8 * cm,
    )
    story: list = []

    story.append(Paragraph("IntelliHire Interview Report", _TITLE))
    story.append(_p(f"Session: {report.get('session_id', 'Unknown')}", _MUTED))
    story.append(_p(
        f"Completed: {report.get('completed_at') or 'Unknown'} · "
        f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
        _MUTED,
    ))

    # --- Overview ---------------------------------------------------------
    story.append(Paragraph("Overview", _H2))
    overview_rows = [
        ["Overall Score", f"{report.get('overall_score', 0)} / 100"],
        ["Questions Evaluated", str(report.get("question_count", 0))],
        ["Status", str(report.get("status", "—"))],
    ]
    overview_table = Table(overview_rows, colWidths=[6 * cm, 10 * cm])
    overview_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(overview_table)

    # --- Topic scores -------------------------------------------------------
    topic_scores = report.get("topic_scores") or []
    if topic_scores:
        story.append(Paragraph("Topic Scores", _H2))
        rows = [["Topic", "Score", "Questions", "Qualitatively Covered"]]
        for t in topic_scores:
            rows.append([
                _cell(t.get("topic_name", "—")),
                f"{t.get('score_100', 0)}/100",
                str(t.get("questions_asked", 0)),
                "Yes" if t.get("qualitatively_covered") else "No",
            ])
        table = Table(rows, colWidths=[6 * cm, 3 * cm, 3 * cm, 4 * cm], repeatRows=1)
        table.setStyle(_TABLE_HEADER_STYLE)
        story.append(table)

    # --- Topic evidence (D-01) ----------------------------------------------
    topic_evidence = report.get("topic_evidence") or []
    if topic_evidence:
        story.append(Paragraph("Topic Evidence", _H2))
        rows = [["Topic", "Final Assessment", "Resume Evidence", "Interview Evidence", "Follow-ups"]]
        for te in topic_evidence:
            skip_reason = te.get("skip_reason")
            rows.append([
                _cell(te.get("topic_name", "—")),
                (te.get("final_assessment") or "—") if not skip_reason else f"Skipped ({skip_reason})",
                te.get("resume_evidence") or "—",
                te.get("interview_evidence") or "—",
                str(te.get("followup_depth", 0)),
            ])
        table = Table(rows, colWidths=[4.5 * cm, 3.5 * cm, 3 * cm, 3 * cm, 2 * cm], repeatRows=1)
        table.setStyle(_TABLE_HEADER_STYLE)
        story.append(table)

    # --- Requirement coverage (D-01) -----------------------------------------
    coverage = report.get("requirement_coverage")
    if coverage:
        story.append(Paragraph("Requirement Coverage", _H2))
        rows = [["Criticality", "Total", "Verified", "Not Verified", "Never Reached"]]
        for criticality, bucket in (coverage.get("by_criticality") or {}).items():
            rows.append([
                criticality,
                str(bucket.get("total", 0)),
                str(bucket.get("verified", 0)),
                str(bucket.get("not_verified", 0)),
                str(bucket.get("never_reached", 0)),
            ])
        table = Table(rows, colWidths=[4 * cm, 3 * cm, 3 * cm, 3 * cm, 3 * cm], repeatRows=1)
        table.setStyle(_TABLE_HEADER_STYLE)
        story.append(table)
        story.append(Spacer(1, 0.2 * cm))
        story.append(_p(
            f"Total topics: {coverage.get('total_topics', 0)} · "
            f"Verified: {coverage.get('total_verified', 0)} · "
            f"Not verified: {coverage.get('total_not_verified', 0)} · "
            f"Never reached: {coverage.get('total_never_reached', 0)}",
            _MUTED,
        ))

    # --- Strengths / weaknesses / improvement suggestions --------------------
    story.append(Paragraph("Strengths", _H2))
    story.append(_bullet_list(report.get("strengths")))

    story.append(Paragraph("Weaknesses", _H2))
    story.append(_bullet_list(report.get("weaknesses")))

    story.append(Paragraph("Improvement Suggestions", _H2))
    story.append(_bullet_list(report.get("improvement_suggestions")))

    if report.get("company_remarks"):
        story.append(Paragraph("Company Remarks", _H2))
        story.append(_p(report["company_remarks"]))

    # --- Detailed question feedback ------------------------------------------
    question_feedback = report.get("question_feedback") or []
    if question_feedback:
        story.append(Paragraph("Detailed Questions & Feedback", _H2))
        rows = [["Topic", "Question", "Difficulty", "Score", "Coverage Signal"]]
        for q in question_feedback:
            rows.append([
                _cell(q.get("topic", "—")),
                _cell(q.get("question", "—")),
                q.get("difficulty") or "—",
                f"{q.get('score_100', 0)}/100",
                q.get("coverage_signal") or "—",
            ])
        table = Table(rows, colWidths=[2.8 * cm, 6.2 * cm, 2 * cm, 1.8 * cm, 3 * cm], repeatRows=1)
        table.setStyle(_TABLE_HEADER_STYLE)
        story.append(table)

    doc.build(story)
    return buffer.getvalue()
