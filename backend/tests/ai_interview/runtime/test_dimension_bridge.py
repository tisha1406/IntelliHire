"""
D-03 prerequisite regression tests.

Proves TopicProgress.dimension is now correctly populated when topics flow
through the REAL pipeline:

    TopicSelector.select_topics()
    -> CoveragePlanner.plan()           (builds TopicBlueprint.source as a
                                          comma-joined TopicSourceCode string,
                                          e.g. "PROJECT_EVIDENCE,RESUME_SKILL")
    -> InterviewBlueprintPlanner.plan() (orchestrates the above)
    -> SessionInitializer.initialize()  (consumes TopicBlueprint.source and
                                          must produce TopicProgress.dimension)

Before this fix, TopicBlueprint.source (TopicSourceCode vocabulary: e.g.
"ROLE_REQUIRED") was parsed by SessionInitializer as if it were a
core.enums.TopicSource value (a different vocabulary: "requirement"), which
always raised ValueError and silently left dimension=None for every topic
produced by this real pipeline -- the only existing test covering this logic
(test_session_strategy_context.py) hand-constructed TopicBlueprint objects
with already-correct TopicSource strings, masking the bug entirely.
"""
import pytest
from datetime import datetime, timezone

from app.ai_interview.blueprint_planning.planner import InterviewBlueprintPlanner
from app.ai_interview.blueprint_planning.topic_selector import TopicSelector
from app.ai_interview.blueprint_planning.coverage_planner import CoveragePlanner
from app.ai_interview.blueprint_planning.priority_allocator import PriorityAllocator
from app.ai_interview.blueprint_planning.difficulty_planner import DifficultyPlanner
from app.ai_interview.blueprint_planning.schemas import (
    BlueprintPlanningRequest, JobRequirementContext,
)
from app.ai_interview.runtime.session_initializer import (
    SessionInitializer, _resolve_dimension_from_source_codes,
)
from app.ai_interview.schemas.interview_mode import (
    InterviewModeDefinition, InterviewModeSettings,
)
from app.ai_interview.core.enums import (
    InterviewModeStatus, TopicDimension, DifficultyLevel, QuestionType,
)
from app.ai_interview.resume_processing.schemas import CandidateInterviewContext
from app.ai_interview.schemas.resume import StructuredResume, Skill, Project, Experience
from app.ai_interview.resume_processing.enums import ExtractionQualityStatus


def _mode(allowed_question_types=None, mode_id="technical"):
    return InterviewModeDefinition(
        mode_id=mode_id, name="Technical", description="d", version=1,
        status=InterviewModeStatus.PUBLISHED,
        settings=InterviewModeSettings(
            allowed_question_types=allowed_question_types or ["initial"],
        ),
        created_at=datetime.now(timezone.utc),
    )


def _candidate_context(skills=None, projects=None, experience=None):
    return CandidateInterviewContext(
        candidate_id="cand1",
        structured_resume=StructuredResume(
            skills=skills or [], projects=projects or [], experience=experience or [],
        ),
        extraction_metadata={
            "source_type": "pdf", "extractor_name": "test", "extractor_version": "1.0",
            "character_count": 100, "detected_sections": [], "warning_count": 0,
            "processing_duration_ms": 1.0,
        },
        quality_status=ExtractionQualityStatus.USABLE,
        warnings=[],
    )


def _build_real_blueprint(job_context, mode, candidate_context):
    """Runs the REAL blueprint_planning pipeline (not hand-constructed
    TopicBlueprint fixtures)."""
    request = BlueprintPlanningRequest(
        candidate_context=candidate_context, mode_definition=mode, job_context=job_context,
    )
    topics = TopicSelector.select_topics(request)
    PriorityAllocator.allocate(topics)
    initial_difficulty = DifficultyPlanner.determine_initial_difficulty(request)
    return CoveragePlanner.plan(request, topics, initial_difficulty)


def _initialize(blueprint, mode_id="technical", campaign_requirements=None, candidate_context=None):
    return SessionInitializer.initialize(
        blueprint=blueprint, candidate_id="cand1", company_id="co1", campaign_id="cam1",
        mode_id=mode_id, mode_version=1,
        campaign_requirements=campaign_requirements, candidate_context=candidate_context,
    )


class TestUnitResolver:
    """Direct unit coverage of _resolve_dimension_from_source_codes, the new
    centralized mapping function, independent of the full pipeline."""

    def test_role_required_maps_to_technical(self):
        assert _resolve_dimension_from_source_codes("ROLE_REQUIRED") == TopicDimension.TECHNICAL

    def test_resume_skill_maps_to_technical(self):
        """Per the architecture doc's own Technical evidence-source
        definition: 'campaign required/preferred skills + resume tech
        stack' -- a resume skill IS technical evidence, not Resume/Experience."""
        assert _resolve_dimension_from_source_codes("RESUME_SKILL") == TopicDimension.TECHNICAL

    def test_project_evidence_maps_to_resume(self):
        assert _resolve_dimension_from_source_codes("PROJECT_EVIDENCE") == TopicDimension.RESUME

    def test_experience_evidence_maps_to_resume(self):
        assert _resolve_dimension_from_source_codes("EXPERIENCE_EVIDENCE") == TopicDimension.RESUME

    def test_mode_required_maps_to_behavioral(self):
        """The only live producer of a MODE_REQUIRED topic today is the
        hardcoded 'Behavioral & Situational' topic in
        TopicSelector.select_topics() -- genuine situational mapping is
        explicitly out of scope for this prerequisite fix (D-03 proper)."""
        assert _resolve_dimension_from_source_codes("MODE_REQUIRED") == TopicDimension.BEHAVIORAL

    def test_unrecognized_or_empty_source_returns_none(self):
        assert _resolve_dimension_from_source_codes("") is None
        assert _resolve_dimension_from_source_codes(None) is None
        assert _resolve_dimension_from_source_codes("NOT_A_REAL_CODE") is None

    def test_multi_source_topic_uses_the_established_priority_allocator_precedence(self):
        """Mirrors PriorityAllocator's own precedence exactly: MODE_REQUIRED
        > ROLE_REQUIRED > PROJECT_EVIDENCE/EXPERIENCE_EVIDENCE > RESUME_SKILL."""
        assert _resolve_dimension_from_source_codes("RESUME_SKILL,ROLE_REQUIRED") == TopicDimension.TECHNICAL
        assert _resolve_dimension_from_source_codes("PROJECT_EVIDENCE,RESUME_SKILL") == TopicDimension.RESUME
        assert _resolve_dimension_from_source_codes("MODE_REQUIRED,ROLE_REQUIRED") == TopicDimension.BEHAVIORAL
        # Order in the string must not matter (CoveragePlanner sorts alphabetically).
        assert _resolve_dimension_from_source_codes("ROLE_REQUIRED,RESUME_SKILL") == TopicDimension.TECHNICAL


class TestRealPipelineEndToEnd:
    """Exercises the REAL TopicSelector -> CoveragePlanner ->
    SessionInitializer chain -- the coverage the task explicitly required
    beyond the old hand-constructed-fixture test."""

    def test_role_required_topic_reaches_technical_dimension(self):
        job_context = JobRequirementContext(
            role_title="Backend Engineer", required_skills=["Python"], interview_duration_minutes=30,
        )
        blueprint = _build_real_blueprint(job_context, _mode(), _candidate_context())
        session = _initialize(blueprint)
        topic = next(t for t in session.topic_progress if blueprint.topics[0].topic_id == t.topic_id)
        assert topic.dimension == TopicDimension.TECHNICAL

    def test_resume_skill_topic_reaches_technical_dimension(self):
        job_context = JobRequirementContext(
            role_title="Backend Engineer", required_skills=[], interview_duration_minutes=30,
        )
        candidate_context = _candidate_context(skills=[Skill(name="Go")])
        blueprint = _build_real_blueprint(job_context, _mode(), candidate_context)
        session = _initialize(blueprint, candidate_context=candidate_context)
        topic = next(t for t in session.topic_progress if t.topic_id == blueprint.topics[0].topic_id)
        assert "ROLE_REQUIRED" not in blueprint.topics[0].source
        assert "RESUME_SKILL" in blueprint.topics[0].source
        assert topic.dimension == TopicDimension.TECHNICAL

    def test_project_evidence_topic_reaches_resume_dimension(self):
        job_context = JobRequirementContext(
            role_title="Backend Engineer", required_skills=[], interview_duration_minutes=30,
        )
        candidate_context = _candidate_context(
            projects=[Project(name="Inventory App", description="d", technologies=["Kubernetes"])]
        )
        blueprint = _build_real_blueprint(job_context, _mode(), candidate_context)
        session = _initialize(blueprint, candidate_context=candidate_context)
        topic = next(t for t in session.topic_progress if t.topic_id == blueprint.topics[0].topic_id)
        assert blueprint.topics[0].source == "PROJECT_EVIDENCE"
        assert topic.dimension == TopicDimension.RESUME

    def test_experience_evidence_topic_reaches_resume_dimension(self):
        job_context = JobRequirementContext(
            role_title="Backend Engineer", required_skills=[], interview_duration_minutes=30,
        )
        candidate_context = _candidate_context(
            experience=[Experience(title="Senior Backend Developer", org="Acme")]
        )
        blueprint = _build_real_blueprint(job_context, _mode(), candidate_context)
        session = _initialize(blueprint, candidate_context=candidate_context)
        topic = next(t for t in session.topic_progress if t.topic_id == blueprint.topics[0].topic_id)
        assert blueprint.topics[0].source == "EXPERIENCE_EVIDENCE"
        assert topic.dimension == TopicDimension.RESUME

    def test_mode_required_topic_reaches_behavioral_dimension(self):
        job_context = JobRequirementContext(
            role_title="Backend Engineer", required_skills=[], interview_duration_minutes=30,
        )
        mode = _mode(allowed_question_types=["behavioral"])
        blueprint = _build_real_blueprint(job_context, mode, _candidate_context())
        session = _initialize(blueprint, mode_id=mode.mode_id)
        behavioral_topic_bp = next(t for t in blueprint.topics if t.topic_name == "Behavioral & Situational")
        assert behavioral_topic_bp.source == "MODE_REQUIRED"
        topic = next(t for t in session.topic_progress if t.topic_id == behavioral_topic_bp.topic_id)
        assert topic.dimension == TopicDimension.BEHAVIORAL

    def test_mixed_style_session_populates_real_dimensions_for_every_topic(self):
        """A single session with role-required, resume-skill, project, and
        mode-required topics all present simultaneously -- representative of
        what a real Mixed-type campaign's blueprint looks like. Every topic
        must get a real (non-None) dimension."""
        job_context = JobRequirementContext(
            role_title="Backend Engineer", required_skills=["Python"], interview_duration_minutes=60,
        )
        candidate_context = _candidate_context(
            skills=[Skill(name="Go")],
            projects=[Project(name="Inventory App", description="d", technologies=["Kubernetes"])],
        )
        mode = _mode(allowed_question_types=["behavioral"])
        blueprint = _build_real_blueprint(job_context, mode, candidate_context)
        session = _initialize(blueprint, mode_id=mode.mode_id, candidate_context=candidate_context)

        assert len(session.topic_progress) > 0
        for topic in session.topic_progress:
            assert topic.dimension is not None, (
                f"topic {topic.topic_id} has no dimension -- the bridge is still broken"
            )

    def test_resolver_can_consume_the_real_dimension_value(self):
        """Confirms the populated dimension is usable exactly where the
        resolver needs it (prompts/resolver.py reads
        QuestionGenerationRequest.dimension, sourced from
        topic_progress.dimension via question_request_builder.py) -- this
        test does not call the resolver itself (out of scope: 'do not modify
        QuestionTurnPlanner'), it proves the *value* QuestionTurnPlanner
        would forward is now a real, resolver-recognized TopicDimension
        member, not None."""
        job_context = JobRequirementContext(
            role_title="Backend Engineer", required_skills=["Python"], interview_duration_minutes=30,
        )
        blueprint = _build_real_blueprint(job_context, _mode(), _candidate_context())
        session = _initialize(blueprint)
        topic = session.topic_progress[0]
        # resolver.py's Mixed-interview branch does:
        #   effective_dimension = request.dimension.value
        # which requires request.dimension to be a real TopicDimension (not None).
        assert topic.dimension is not None
        assert topic.dimension.value in {"technical", "resume", "behavioral", "situational"}


class TestNoRegressionForSingleTypeBehavior:
    """Single-type (non-Mixed) campaigns never consulted topic.dimension for
    prompt resolution (resolver.py uses the campaign's interview_type
    instead) -- this fix must not change that path's behavior at all."""

    def test_technical_only_session_still_initializes_correctly(self):
        job_context = JobRequirementContext(
            role_title="Backend Engineer", required_skills=["Python", "Docker"],
            interview_duration_minutes=30,
        )
        blueprint = _build_real_blueprint(job_context, _mode(), _candidate_context())
        session = _initialize(
            blueprint, campaign_requirements=[{"skill": "Python", "criticality": "critical"}],
        )
        python_topic_bp = next(t for t in blueprint.topics if t.topic_name == "Python")
        python_progress = next(t for t in session.topic_progress if t.topic_id == python_topic_bp.topic_id)
        # Existing, unaffected behavior: criticality still resolves correctly.
        from app.ai_interview.core.enums import RequirementCriticality
        assert python_progress.criticality == RequirementCriticality.CRITICAL
        # New, now-fixed behavior: dimension is also populated.
        assert python_progress.dimension == TopicDimension.TECHNICAL
