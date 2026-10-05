"""
Phase 5 — Question Orchestration & Interview Turn Engine

QuestionRequestBuilder: Constructs the minimal, deterministic QuestionGenerationRequest
from a QuestionTurnPlan, CandidateInterviewContext, and InterviewModeDefinition.

Context minimization strategy:
  - Only skills, projects, and experience whose name/title/technologies contain
    the topic name (case-insensitive) are included.
  - Unrelated resume sections are excluded.
  - Previous questions are bounded by MAX_PREVIOUS_QUESTIONS_CONTEXT and ordered
    by most-recently-dispatched (deterministic LIFO slice).
  - selected_question_type is deterministically chosen as the first element of
    allowed_question_types (same input → same selection).
"""
from app.ai_interview.question_engine.config import QuestionEngineConfig
from app.ai_interview.question_engine.schemas import (
    QuestionTurnPlan,
    QuestionGenerationRequest,
)
from app.ai_interview.resume_processing.schemas import CandidateInterviewContext
from app.ai_interview.schemas.interview_mode import InterviewModeDefinition
from app.ai_interview.core.enums import QuestionType


class QuestionRequestBuilder:
    """
    Builds a bounded, deterministic QuestionGenerationRequest.

    Same inputs → same request.  No mutations.  No side effects.
    """

    @staticmethod
    def build(
        plan: QuestionTurnPlan,
        candidate_context: CandidateInterviewContext,
        mode: InterviewModeDefinition,
        question_history: list,  # List[QuestionRecord] — kept as list[Any] to avoid circular import
        evaluation_history: list = None,  # List[EvaluationRecord]
    ) -> QuestionGenerationRequest:
        """
        Construct a QuestionGenerationRequest from the deterministic turn plan.

        Args:
            plan:               Approved QuestionTurnPlan (allowed=True).
            candidate_context:  Structured resume context from Phase 2.
            mode:               InterviewModeDefinition from Phase 1.
            question_history:   Session's official QuestionRecord list.
            evaluation_history: Session's official EvaluationRecord list.
        """
        if not plan.allowed:
            raise ValueError(
                "QuestionRequestBuilder.build() called with a denied QuestionTurnPlan. "
                "Check plan.allowed before calling the builder."
            )

        resume = candidate_context.structured_resume
        topic_keyword = plan.topic_name.lower()

        # ── Relevant skills ──────────────────────────────────────────────────
        relevant_skills = [
            skill.name
            for skill in resume.skills
            if topic_keyword in skill.name.lower()
            or (skill.category and topic_keyword in skill.category.lower())
        ]

        # ── Relevant projects ────────────────────────────────────────────────
        relevant_projects = [
            f"{proj.name}: {proj.description}"
            for proj in resume.projects
            if topic_keyword in proj.name.lower()
            or topic_keyword in proj.description.lower()
            or any(topic_keyword in tech.lower() for tech in proj.technologies)
        ]

        # ── Relevant experience ──────────────────────────────────────────────
        relevant_experience = [
            f"{exp.title} at {exp.org}"
            + (f": {exp.description}" if exp.description else "")
            for exp in resume.experience
            if topic_keyword in exp.title.lower()
            or (exp.description and topic_keyword in exp.description.lower())
        ]

        # ── Job requirements ─────────────────────────────────────────────────
        relevant_job_requirements: list[str] = [plan.campaign_requirement] if plan.campaign_requirement else []

        # ── Previous questions (bounded LIFO) ────────────────────────────────
        # Take the last MAX_PREVIOUS_QUESTIONS_CONTEXT dispatched questions,
        # regardless of topic, to prevent cross-topic repetition.
        max_ctx = QuestionEngineConfig.MAX_PREVIOUS_QUESTIONS_CONTEXT
        recent_records = question_history[-max_ctx:] if len(question_history) > max_ctx else list(question_history)
        # Deterministic: order preserved as-dispatched
        previous_questions = [r.question_text for r in recent_records]

        # ── selected_question_type ────────────────────────────────────────────
        # Deterministic: always pick the first allowed type.
        # This ensures same plan → same selected type.
        if plan.allowed_question_types:
            selected_type: QuestionType = plan.allowed_question_types[0]
        else:
            selected_type = QuestionType.INITIAL
            
        # ── Previous turn context for follow-ups ─────────────────────────────
        evaluation_history = evaluation_history or []
        previous_question_for_followup = None
        previous_answer = None
        previous_evaluation = None
        
        # We only pass follow-up context if this is a follow-up category
        if plan.category and plan.category.value.startswith("followup"):
            if question_history and evaluation_history:
                last_eval = evaluation_history[-1]
                matched_q = next((q for q in question_history if q.record_id == last_eval.question_record_id), None)
                if matched_q:
                    previous_question_for_followup = matched_q.question_text
                    # The candidate's submitted answer is persisted on the evaluation of that
                    # question (EvaluationRecord.answer_text, whitespace-normalised, set by
                    # EvaluationApplicator). Only hand it to the prompt when that evaluation is
                    # for THIS plan's topic, so a follow-up never sees another topic's answer.
                    if last_eval.topic_id == plan.topic_id:
                        previous_answer = last_eval.answer_text or None
                    
                    previous_evaluation = {
                        "score": last_eval.overall_score,
                        "correctness": last_eval.correctness,
                        "coverage": last_eval.coverage,
                        "confidence": last_eval.confidence,
                        "qualitative_coverage_signal": last_eval.qualitative_coverage_signal.value if hasattr(last_eval.qualitative_coverage_signal, 'value') else last_eval.qualitative_coverage_signal,
                        "evidence_quality": last_eval.evidence_quality,
                        "followup_recommended": last_eval.followup_recommended,
                    }

        return QuestionGenerationRequest(
            session_id=plan.session_id,
            turn_number=plan.turn_number,
            topic_id=plan.topic_id,
            topic_name=plan.topic_name,
            mode_id=mode.mode_id,
            question_style=plan.question_style or mode.settings.question_style or "technical",
            interview_type=plan.interview_type,
            strategy=plan.strategy,
            strategy_id=plan.strategy_id,
            dimension=plan.dimension,
            category=plan.category,
            resume_evidence=plan.resume_evidence,
            candidate_claim=plan.candidate_claim,
            interview_evidence=plan.interview_evidence,
            campaign_requirement=plan.campaign_requirement,
            requirement_criticality=plan.requirement_criticality,
            scenario_context=plan.scenario_context,
            specificity_required=plan.specificity_required,
            difficulty=plan.difficulty,
            allowed_question_types=plan.allowed_question_types,
            selected_question_type=selected_type,
            relevant_skills=relevant_skills,
            relevant_projects=relevant_projects,
            relevant_experience=relevant_experience,
            previous_questions=previous_questions,
            previous_question_for_followup=previous_question_for_followup,
            previous_answer=previous_answer,
            previous_evaluation=previous_evaluation,
            question_number=plan.topic_questions_asked + 1,
            max_questions_for_topic=plan.topic_question_budget,
        )
