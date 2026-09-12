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
    ) -> QuestionGenerationRequest:
        """
        Construct a QuestionGenerationRequest from the deterministic turn plan.

        Args:
            plan:               Approved QuestionTurnPlan (allowed=True).
            candidate_context:  Structured resume context from Phase 2.
            mode:               InterviewModeDefinition from Phase 1.
            question_history:   Session's official QuestionRecord list.
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
        # Phase 5 defers job-requirement context to a future phase.
        # JobRequirementContext will be added when the candidate-role matching
        # pipeline is integrated. For now, always empty.
        relevant_job_requirements: list[str] = []

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

        return QuestionGenerationRequest(
            session_id=plan.session_id,
            turn_number=plan.turn_number,
            topic_id=plan.topic_id,
            topic_name=plan.topic_name,
            difficulty=plan.difficulty,
            allowed_question_types=plan.allowed_question_types,
            selected_question_type=selected_type,
            relevant_skills=relevant_skills,
            relevant_projects=relevant_projects,
            relevant_experience=relevant_experience,
            relevant_job_requirements=relevant_job_requirements,
            previous_questions=previous_questions,
            question_number=plan.topic_questions_asked + 1,
            max_questions_for_topic=plan.topic_question_budget,
        )
