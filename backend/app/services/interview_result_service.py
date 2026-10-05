"""
InterviewResultService
======================
READ / AGGREGATION LAYER ONLY.

Reads the authoritative InterviewSessionSchema persisted by the AI Interview
Engine and projects it into a result report for Candidate and Company
frontends.

Architecture rules:
- Does NOT call the LLM.
- Does NOT mutate interview state.
- Does NOT re-evaluate answers.
- All data comes exclusively from session.evaluation_history,
  session.question_history, and session.blueprint.
"""

import logging
from typing import Dict, Any, List, Optional

from app.db.mongo import get_database
from app.ai_interview.persistence.repository import InterviewSessionRepository
from app.ai_interview.persistence.exceptions import SessionNotFoundError
from app.ai_interview.schemas.session import InterviewSessionSchema, TopicProgress
from app.ai_interview.question_engine.schemas import QuestionRecord
from app.ai_interview.answer_engine.schemas import EvaluationRecord
from app.ai_interview.schemas.blueprint import TopicBlueprint
from app.ai_interview.core.enums import InterviewEvidence, RequirementCriticality
# Reused verbatim from the dispatcher so the report's notion of "a follow-up
# category" never drifts from the engine's own (QuestionDispatcher is the
# single authority that decides which categories count as follow-ups).
from app.ai_interview.question_engine.question_dispatcher import _FOLLOWUP_CATEGORIES

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# D-01: final_assessment vocabulary.
#
# Not an engine concept — this is a report-aggregation-layer rollup, so it
# intentionally lives here rather than in app/ai_interview/core/enums.py,
# keeping the deterministic engine's own enum surface untouched.
#
# Distinct from TopicProgress.interview_evidence: interview_evidence is
# overwritten to the single MOST RECENT evaluation's signal every time
# EvaluationApplicator applies a new answer (see evaluation_applicator.py:
# "if evaluation.interview_evidence: topic_progress.interview_evidence = ...").
# final_assessment instead summarizes the WHOLE topic by reusing the already-
# computed TopicEvaluationAggregate.average_score, classified with the exact
# same 0.8 / 0.5 / 0.3 thresholds EvaluationApplicator itself already applies
# per-answer (strong_answers / partial_answers / weak_answers /
# insufficient_answers buckets) -- applied once at topic-aggregate level
# instead of per-answer. No new thresholds, no new scoring model, no LLM call,
# and candidate_claim is never consulted (a claim is never proof).
# ---------------------------------------------------------------------------
_FINAL_ASSESSMENT_STRONG = "strong"
_FINAL_ASSESSMENT_ACCEPTABLE = "acceptable"
_FINAL_ASSESSMENT_BASIC = "basic"
_FINAL_ASSESSMENT_INSUFFICIENT = "insufficient"
_FINAL_ASSESSMENT_NOT_DEMONSTRATED = "not_demonstrated"


def _derive_final_assessment(tp: TopicProgress) -> str:
    """Deterministic topic-level rollup. See module docstring above for the
    full rationale and why this is distinct from interview_evidence."""
    agg = tp.evaluation_aggregate
    if agg.answers_evaluated == 0:
        return _FINAL_ASSESSMENT_NOT_DEMONSTRATED
    if agg.average_score >= 0.8:
        return _FINAL_ASSESSMENT_STRONG
    if agg.average_score >= 0.5:
        return _FINAL_ASSESSMENT_ACCEPTABLE
    if agg.average_score >= 0.3:
        return _FINAL_ASSESSMENT_BASIC
    return _FINAL_ASSESSMENT_INSUFFICIENT


# ---------------------------------------------------------------------------
# Score conversion: engine uses 0.0–1.0, frontend expects 0–100
# ---------------------------------------------------------------------------
def _to_100(score_01: float) -> int:
    """Clamp and scale a 0.0–1.0 score to an integer 0–100."""
    return int(round(max(0.0, min(1.0, score_01)) * 100))


def _deduplicate(items: List[str]) -> List[str]:
    """Deduplicate a list of strings preserving insertion order."""
    seen: set = set()
    result: List[str] = []
    for item in items:
        key = item.strip().lower()
        if key not in seen:
            seen.add(key)
            result.append(item.strip())
    return result


class InterviewResultService:
    """
    Aggregates the final interview report from an InterviewSessionSchema.

    Uses the AI engine's own InterviewSessionRepository so it reads the
    identical document that the engine writes (queried by session_id field,
    not MongoDB _id).
    """

    def __init__(self):
        db = get_database()
        self._engine_repo = InterviewSessionRepository(db.interview_sessions)

    # -----------------------------------------------------------------------
    # Public API
    # -----------------------------------------------------------------------

    async def generate_result_report(self, session_id: str) -> Dict[str, Any]:
        """
        Build a result report dict from a completed InterviewSessionSchema.

        Returned keys:
            session_id              str
            status                  "COMPLETED" | "IN_PROGRESS" | "COMPLETED_NO_DATA"
            has_report              bool
            overall_score           int  (0-100, mean of all question scores)
            question_count          int
            completed_at            str | None  (ISO-8601)
            question_feedback       list[dict]  (per-question detail)
            topic_scores            list[dict]  (per-topic aggregate)
            strengths               list[str]
            weaknesses              list[str]
            improvement_suggestions list[str]
            company_remarks         str   (kept for transport_service compatibility)
            requirement_coverage    dict  (D-01: session-level criticality tally)
            topic_evidence          list[dict]  (D-01: per-topic evidence block,
                                                   see below — a sibling list to
                                                   topic_scores, NOT merged into it)

        topic_scores is UNCHANGED by D-01 — its "questions_asked" remains the
        existing int count, exactly as before.

        topic_evidence (D-01, new, covers every topic in session.topic_progress
        including ones never reached) — each dict carries:
            topic_id, topic_name
            questions_asked           list[dict]   (the actual dispatched
                                                      question records for this
                                                      topic, per specs.md's
                                                      required field name —
                                                      intentionally a different
                                                      container from
                                                      topic_scores[].questions_asked)
            resume_evidence           str | None   ("absent"|"partial"|"strong")
            candidate_claim           str | None   (not proof; never scored)
            interview_evidence        str | None   (AnswerEngine's own record)
            final_assessment          str          (topic-aggregate rollup; see
                                                      _derive_final_assessment)
            followup_depth            int          (= TopicProgress.follow_up_count)
            followup_categories_used  list[str]    (follow-up categories actually
                                                      dispatched on this topic)
            skip_reason               str | None   (only set when the topic was
                                                      never attempted)

        All previously hardcoded mock scores
        (communication_score, confidence, problem_solving, soft_skills_score,
        time_management, resume_match, radar_data) have been removed.
        """
        session = await self._load_session(session_id)

        # --- Incomplete session ---
        from app.ai_interview.core.enums import InterviewState
        if session.state not in (InterviewState.COMPLETED,):
            return {
                "session_id": session_id,
                "status": "IN_PROGRESS",
                "has_report": False,
                "message": "Interview is not yet completed.",
            }

        # --- Build lookup indexes ---
        question_index: Dict[str, QuestionRecord] = {
            q.record_id: q for q in session.question_history
        }
        topic_index: Dict[str, TopicBlueprint] = {
            t.topic_id: t for t in session.blueprint.topics
        }
        topic_progress_index: Dict[str, TopicProgress] = {
            tp.topic_id: tp for tp in session.topic_progress
        }

        evaluations: List[EvaluationRecord] = session.evaluation_history

        if not evaluations:
            return {
                "session_id": session_id,
                "status": "COMPLETED_NO_DATA",
                "has_report": False,
                "message": "Interview completed but no evaluations were recorded.",
            }

        # --- Per-question feedback ---
        question_feedback = self._build_question_feedback(
            evaluations, question_index, topic_index
        )

        # --- Overall score: arithmetic mean of all question overall_scores ---
        avg_score_01 = sum(ev.overall_score for ev in evaluations) / len(evaluations)
        overall_score_100 = _to_100(avg_score_01)

        # --- Per-topic scores (from TopicProgress.evaluation_aggregate) —
        #     unchanged shape, "questions_asked" here remains the existing
        #     int count. ---
        topic_scores = self._build_topic_scores(
            evaluations, topic_progress_index, topic_index
        )

        # --- Strengths / weaknesses from persisted score signals ---
        strengths, weaknesses = self._build_qualitative_summary(
            evaluations, topic_index
        )

        # --- Improvement suggestions from weak-topic aggregates ---
        improvement_suggestions = self._build_improvement_suggestions(topic_scores)

        # --- D-01: session-level requirement-coverage summary, derived purely
        #     from already-persisted TopicProgress fields (criticality,
        #     interview_evidence, qualitatively_covered, questions_asked).
        #     A candidate_claim never counts toward "verified" on its own. ---
        requirement_coverage = self._build_requirement_coverage_summary(
            session.topic_progress
        )

        # --- D-01: per-topic evidence block — a separate sibling list to
        #     topic_scores (does not reuse or rename its "questions_asked"
        #     int field). Covers every topic in session.topic_progress,
        #     including ones never reached (skip_reason). ---
        topic_evidence = self._build_topic_evidence(
            session.topic_progress, topic_index, session.question_history
        )

        return {
            "session_id": session_id,
            "status": "COMPLETED",
            "has_report": True,
            "overall_score": overall_score_100,
            "question_count": len(evaluations),
            "completed_at": (
                session.completed_at.isoformat() if session.completed_at else None
            ),
            "question_feedback": question_feedback,
            "topic_scores": topic_scores,
            "strengths": strengths,
            "weaknesses": weaknesses,
            "improvement_suggestions": improvement_suggestions,
            # Kept for backward compatibility with transport_service caller
            "company_remarks": "AI Evaluation Completed.",
            # D-01: session-level evidence/coverage summary (additive).
            "requirement_coverage": requirement_coverage,
            # D-01: per-topic evidence block (additive, separate from topic_scores).
            "topic_evidence": topic_evidence,
        }

    # -----------------------------------------------------------------------
    # Private helpers
    # -----------------------------------------------------------------------

    async def _load_session(self, session_id: str) -> InterviewSessionSchema:
        """
        Load via the engine's InterviewSessionRepository (queries by
        session_id field, not MongoDB _id).  Normalises the exception so
        callers don't need to import persistence-layer errors.
        """
        try:
            return await self._engine_repo.get_by_id(session_id)
        except SessionNotFoundError:
            raise ValueError(f"Session {session_id} not found")
        except Exception as exc:
            logger.error(
                "Unexpected error loading session %s for result report: %s",
                session_id,
                exc,
                exc_info=True,
            )
            raise

    def _build_question_feedback(
        self,
        evaluations: List[EvaluationRecord],
        question_index: Dict[str, QuestionRecord],
        topic_index: Dict[str, TopicBlueprint],
    ) -> List[Dict[str, Any]]:
        feedback = []
        for idx, ev in enumerate(evaluations, start=1):
            q: Optional[QuestionRecord] = question_index.get(ev.question_record_id)
            t: Optional[TopicBlueprint] = topic_index.get(ev.topic_id)

            feedback.append(
                {
                    "id": str(idx),
                    "question_record_id": ev.question_record_id,
                    "topic_id": ev.topic_id,
                    "topic": t.topic_name if t else ev.topic_id,
                    "question": q.question_text if q else "Question record not found",
                    "difficulty": q.difficulty.value if q else None,
                    "question_type": q.question_type.value if q else None,
                    # 0.0–1.0 for company/candidates.py callers that multiply by 10
                    "score": round(ev.overall_score, 2),
                    # 0–100 for direct display
                    "score_100": _to_100(ev.overall_score),
                    "coverage_signal": (
                        ev.qualitative_coverage_signal.value
                        if ev.qualitative_coverage_signal
                        else None
                    ),
                    "follow_up_signal": (
                        ev.follow_up_signal.value if ev.follow_up_signal else None
                    ),
                    "evaluated_at": (
                        ev.timestamp.isoformat() if ev.timestamp else None
                    ),
                }
            )
        return feedback

    def _build_topic_scores(
        self,
        evaluations: List[EvaluationRecord],
        topic_progress_index: Dict[str, TopicProgress],
        topic_index: Dict[str, TopicBlueprint],
    ) -> List[Dict[str, Any]]:
        evaluated_topic_ids = {ev.topic_id for ev in evaluations}
        result = []
        for topic_id in evaluated_topic_ids:
            tp: Optional[TopicProgress] = topic_progress_index.get(topic_id)
            bt: Optional[TopicBlueprint] = topic_index.get(topic_id)
            if not tp:
                continue
            agg = tp.evaluation_aggregate
            result.append(
                {
                    "topic_id": topic_id,
                    "topic_name": bt.topic_name if bt else topic_id,
                    "questions_asked": tp.questions_asked,
                    "answers_evaluated": agg.answers_evaluated,
                    "average_score": round(agg.average_score, 2),
                    "score_100": _to_100(agg.average_score),
                    "strong_answers": agg.strong_answers,
                    "partial_answers": agg.partial_answers,
                    "weak_answers": agg.weak_answers,
                    "insufficient_answers": agg.insufficient_answers,
                    "qualitatively_covered": tp.qualitatively_covered,
                    "coverage_score": round(tp.coverage_score, 2),
                }
            )
        result.sort(key=lambda x: x["topic_name"])
        return result

    def _build_topic_evidence(
        self,
        topic_progress_list: List[TopicProgress],
        topic_index: Dict[str, TopicBlueprint],
        question_history: List[QuestionRecord],
    ) -> List[Dict[str, Any]]:
        """
        D-01 evidence-model block — a separate per-topic list, sibling to
        topic_scores, so the pre-existing topic_scores[].questions_asked
        (an int count) is never renamed or overloaded.

        Covers ALL of session.topic_progress (not just topics that received
        an evaluation), so a topic that was never reached still appears here
        with questions_asked=[] and a populated skip_reason.
        """
        result = []
        for tp in topic_progress_list:
            bt: Optional[TopicBlueprint] = topic_index.get(tp.topic_id)

            # The actual persisted question records dispatched for this
            # topic, in dispatch order. Required field name per specs.md:
            # "questions_asked" (a list here — distinct container from
            # topic_scores[].questions_asked, the int count).
            topic_questions = sorted(
                (q for q in question_history if q.topic_id == tp.topic_id),
                key=lambda q: q.turn_number,
            )
            questions_asked = [
                {
                    "record_id": q.record_id,
                    "question_text": q.question_text,
                    "question_type": q.question_type.value if q.question_type else None,
                    "difficulty": q.difficulty.value if q.difficulty else None,
                    "category": q.category.value if q.category else None,
                    "turn_number": q.turn_number,
                    "asked_at": q.asked_at.isoformat() if q.asked_at else None,
                }
                for q in topic_questions
            ]

            # Only categories actually used by follow-up questions on this
            # topic, deduplicated, in the order first encountered.
            # _FOLLOWUP_CATEGORIES is reused verbatim from QuestionDispatcher
            # (the single existing authority on what counts as a follow-up).
            followup_categories_used: List[str] = []
            for q in topic_questions:
                if q.category in _FOLLOWUP_CATEGORIES and q.category.value not in followup_categories_used:
                    followup_categories_used.append(q.category.value)

            result.append(
                {
                    "topic_id": tp.topic_id,
                    "topic_name": bt.topic_name if bt else tp.topic_id,
                    "questions_asked": questions_asked,
                    "resume_evidence": tp.resume_evidence.value if tp.resume_evidence else None,
                    "candidate_claim": tp.candidate_claim,
                    "interview_evidence": tp.interview_evidence.value if tp.interview_evidence else None,
                    "final_assessment": _derive_final_assessment(tp),
                    # TopicProgress.follow_up_count: incremented ONLY by
                    # QuestionDispatcher/FollowUpPolicyEngine when a follow-up
                    # category is actually dispatched — the engine's own
                    # explicit follow-up counter, not inferred from question count.
                    "followup_depth": tp.follow_up_count,
                    "followup_categories_used": followup_categories_used,
                    # Only meaningful for topics that were never attempted;
                    # None otherwise — never a fabricated reason.
                    "skip_reason": (
                        tp.terminal_reason.value
                        if tp.questions_asked == 0 and tp.terminal_reason
                        else None
                    ),
                }
            )
        result.sort(key=lambda x: x["topic_name"])
        return result

    def _build_requirement_coverage_summary(
        self, topic_progress_list: List[TopicProgress]
    ) -> Dict[str, Any]:
        """
        D-01: session-level requirement-coverage tally, derived purely from
        already-persisted TopicProgress fields. Deterministic counts only —
        no new scoring model.

        Per topic, bucketed by RequirementCriticality:
          - "never_reached"  : questions_asked == 0 (topic was skipped)
          - "verified"       : attempted AND qualitatively_covered AND
                                interview_evidence in (ACCEPTABLE, STRONG)
                                (a candidate_claim alone never counts here —
                                only interview_evidence, the AnswerEngine's
                                own record of what was demonstrated, does)
          - "not_verified"   : attempted but the above bar was not met
        """
        criticality_labels = [c.value for c in RequirementCriticality]
        by_criticality: Dict[str, Dict[str, int]] = {
            label: {"total": 0, "verified": 0, "not_verified": 0, "never_reached": 0}
            for label in criticality_labels
        }
        by_criticality["unspecified"] = {"total": 0, "verified": 0, "not_verified": 0, "never_reached": 0}

        _verified_evidence = {InterviewEvidence.ACCEPTABLE, InterviewEvidence.STRONG}

        for tp in topic_progress_list:
            label = tp.criticality.value if tp.criticality else "unspecified"
            bucket = by_criticality.setdefault(
                label, {"total": 0, "verified": 0, "not_verified": 0, "never_reached": 0}
            )
            bucket["total"] += 1

            if tp.questions_asked == 0:
                bucket["never_reached"] += 1
            elif tp.qualitatively_covered and tp.interview_evidence in _verified_evidence:
                bucket["verified"] += 1
            else:
                bucket["not_verified"] += 1

        return {
            "by_criticality": by_criticality,
            "total_topics": len(topic_progress_list),
            "total_verified": sum(b["verified"] for b in by_criticality.values()),
            "total_not_verified": sum(b["not_verified"] for b in by_criticality.values()),
            "total_never_reached": sum(b["never_reached"] for b in by_criticality.values()),
        }

    def _build_qualitative_summary(
        self,
        evaluations: List[EvaluationRecord],
        topic_index: Dict[str, TopicBlueprint],
    ):
        """
        Derive strengths and weaknesses from the persisted score signals.

        Note: EvaluationRecord (the only persisted evaluation artifact) does
        NOT carry free-text strengths/weaknesses — those live on EvaluationResult
        which is in-memory only and is not persisted separately.
        Qualitative strings are therefore derived from the quantitative signals
        that ARE persisted (overall_score thresholds).
        """
        strengths: List[str] = []
        weaknesses: List[str] = []

        for ev in evaluations:
            t: Optional[TopicBlueprint] = topic_index.get(ev.topic_id)
            topic_name = t.topic_name if t else ev.topic_id
            score_100 = _to_100(ev.overall_score)

            if ev.overall_score >= 0.8:
                strengths.append(
                    f"Strong performance in {topic_name} ({score_100}/100)"
                )
            elif ev.overall_score < 0.5:
                weaknesses.append(
                    f"Needs improvement in {topic_name} ({score_100}/100)"
                )

        strengths = _deduplicate(strengths)
        weaknesses = _deduplicate(weaknesses)

        if not strengths:
            strengths = ["Completed all interview questions"]
        if not weaknesses:
            weaknesses = ["No major weaknesses identified from evaluation signals"]

        return strengths, weaknesses

    def _build_improvement_suggestions(
        self, topic_scores: List[Dict[str, Any]]
    ) -> List[str]:
        """Build improvement suggestions from persisted aggregate data only."""
        suggestions = []
        for ts in topic_scores:
            if ts.get("weak_answers", 0) > 0 or ts.get("insufficient_answers", 0) > 0:
                suggestions.append(
                    f"Practice elaborating on {ts['topic_name']} "
                    f"(scored {ts['score_100']}/100)"
                )
        if not suggestions:
            suggestions = [
                "Continue to practise explaining problem-solving approaches in depth."
            ]
        return suggestions


