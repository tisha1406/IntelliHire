"""
D-03 prerequisite #2 regression tests.

Proves TopicProgress.source is now correctly populated (core.enums.TopicSource:
resume | requirement | gap | behavioral) when topics flow through the REAL
pipeline:

    TopicSelector.select_topics()
    -> CoveragePlanner.plan()           (builds TopicBlueprint.source as a
                                          comma-joined TopicSourceCode string)
    -> InterviewBlueprintPlanner.plan()
    -> SessionInitializer.initialize()  (consumes TopicBlueprint.source +
                                          resume_evidence and must produce
                                          TopicProgress.source)

Before this fix, TopicBlueprint.source (TopicSourceCode vocabulary, e.g.
"ROLE_REQUIRED") was parsed by SessionInitializer as if it were already a
core.enums.TopicSource value (e.g. "requirement") -- a different vocabulary --
which always raised ValueError and silently left source=None for every topic
produced by the real pipeline. This also made question_turn_planner.py's
GAP_VERIFICATION routing (line ~130: `if topic_progress.source ==
TopicSource.GAP`) permanently unreachable, since source was never anything
but None.

GAP is not a literal TopicSourceCode -- it is the DERIVED combination of
ROLE_REQUIRED + ResumeEvidence.ABSENT (a campaign-required skill missing from
the resume), per specs.md:166 ("Gap verification (resume-absent
requirements)") and prompt_library.py's S_GAP_VERIFICATION text ("verifying a
specific campaign requirement that lacks clear resume evidence"). See
_resolve_topic_source_from_source_codes in session_initializer.py for the
full mapping justification.
"""
from datetime import datetime, timezone

from app.ai_interview.blueprint_planning.topic_selector import TopicSelector
from app.ai_interview.blueprint_planning.coverage_planner import CoveragePlanner
from app.ai_interview.blueprint_planning.priority_allocator import PriorityAllocator
from app.ai_interview.blueprint_planning.difficulty_planner import DifficultyPlanner
from app.ai_interview.blueprint_planning.schemas import (
    BlueprintPlanningRequest, JobRequirementContext,
)
from app.ai_interview.runtime.session_initializer import (
    SessionInitializer, _resolve_topic_source_from_source_codes,
)
from app.ai_interview.schemas.interview_mode import (
    InterviewModeDefinition, InterviewModeSettings,
)
from app.ai_interview.core.enums import (
    InterviewModeStatus, TopicSource, ResumeEvidence, QuestionCategory, InterviewState,
)
from app.ai_interview.question_engine.question_turn_planner import QuestionTurnPlanner
from app.ai_interview.runtime.schemas import RuntimeDecision
from app.ai_interview.runtime.enums import RuntimeAction
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
    """Direct unit coverage of _resolve_topic_source_from_source_codes."""

    def test_role_required_with_absent_resume_evidence_maps_to_gap(self):
        assert _resolve_topic_source_from_source_codes(
            "ROLE_REQUIRED", ResumeEvidence.ABSENT
        ) == TopicSource.GAP

    def test_role_required_with_strong_resume_evidence_maps_to_requirement(self):
        assert _resolve_topic_source_from_source_codes(
            "ROLE_REQUIRED", ResumeEvidence.STRONG
        ) == TopicSource.REQUIREMENT

    def test_role_required_with_partial_resume_evidence_maps_to_requirement(self):
        assert _resolve_topic_source_from_source_codes(
            "ROLE_REQUIRED", ResumeEvidence.PARTIAL
        ) == TopicSource.REQUIREMENT

    def test_resume_skill_maps_to_resume_regardless_of_resume_evidence(self):
        assert _resolve_topic_source_from_source_codes(
            "RESUME_SKILL", ResumeEvidence.ABSENT
        ) == TopicSource.RESUME
        assert _resolve_topic_source_from_source_codes(
            "RESUME_SKILL", ResumeEvidence.STRONG
        ) == TopicSource.RESUME

    def test_project_evidence_maps_to_resume(self):
        assert _resolve_topic_source_from_source_codes(
            "PROJECT_EVIDENCE", ResumeEvidence.STRONG
        ) == TopicSource.RESUME

    def test_experience_evidence_maps_to_resume(self):
        assert _resolve_topic_source_from_source_codes(
            "EXPERIENCE_EVIDENCE", ResumeEvidence.STRONG
        ) == TopicSource.RESUME

    def test_mode_required_maps_to_behavioral(self):
        assert _resolve_topic_source_from_source_codes(
            "MODE_REQUIRED", ResumeEvidence.ABSENT
        ) == TopicSource.BEHAVIORAL

    def test_unrecognized_or_empty_source_returns_none(self):
        assert _resolve_topic_source_from_source_codes("", ResumeEvidence.ABSENT) is None
        assert _resolve_topic_source_from_source_codes(None, ResumeEvidence.ABSENT) is None
        assert _resolve_topic_source_from_source_codes("NOT_A_REAL_CODE", ResumeEvidence.ABSENT) is None

    def test_multi_source_topic_uses_the_established_precedence(self):
        """Same precedence as the dimension bridge: MODE_REQUIRED >
        ROLE_REQUIRED > PROJECT_EVIDENCE/EXPERIENCE_EVIDENCE > RESUME_SKILL."""
        assert _resolve_topic_source_from_source_codes(
            "RESUME_SKILL,ROLE_REQUIRED", ResumeEvidence.ABSENT
        ) == TopicSource.GAP
        assert _resolve_topic_source_from_source_codes(
            "RESUME_SKILL,ROLE_REQUIRED", ResumeEvidence.STRONG
        ) == TopicSource.REQUIREMENT
        assert _resolve_topic_source_from_source_codes(
            "MODE_REQUIRED,ROLE_REQUIRED", ResumeEvidence.ABSENT
        ) == TopicSource.BEHAVIORAL
        assert _resolve_topic_source_from_source_codes(
            "PROJECT_EVIDENCE,RESUME_SKILL", ResumeEvidence.ABSENT
        ) == TopicSource.RESUME


class TestRealPipelineEndToEnd:
    """Exercises the REAL TopicSelector -> CoveragePlanner ->
    SessionInitializer chain for every TopicSourceCode."""

    def test_role_required_absent_from_resume_reaches_gap(self):
        job_context = JobRequirementContext(
            role_title="Backend Engineer", required_skills=["Python"], interview_duration_minutes=30,
        )
        blueprint = _build_real_blueprint(job_context, _mode(), _candidate_context())
        session = _initialize(
            blueprint, campaign_requirements=[{"skill": "Python", "criticality": "critical"}],
        )
        topic = next(t for t in session.topic_progress if t.topic_id == blueprint.topics[0].topic_id)
        assert topic.resume_evidence == ResumeEvidence.ABSENT
        assert topic.source == TopicSource.GAP

    def test_role_required_present_on_resume_reaches_requirement(self):
        job_context = JobRequirementContext(
            role_title="Backend Engineer", required_skills=["Python"], interview_duration_minutes=30,
        )
        candidate_context = _candidate_context(skills=[Skill(name="Python")])
        blueprint = _build_real_blueprint(job_context, _mode(), candidate_context)
        session = _initialize(
            blueprint,
            campaign_requirements=[{"skill": "Python", "criticality": "critical"}],
            candidate_context=candidate_context,
        )
        topic = next(t for t in session.topic_progress if t.topic_id == blueprint.topics[0].topic_id)
        assert topic.resume_evidence == ResumeEvidence.STRONG
        assert topic.source == TopicSource.REQUIREMENT

    def test_resume_skill_topic_reaches_resume_source(self):
        job_context = JobRequirementContext(
            role_title="Backend Engineer", required_skills=[], interview_duration_minutes=30,
        )
        candidate_context = _candidate_context(skills=[Skill(name="Go")])
        blueprint = _build_real_blueprint(job_context, _mode(), candidate_context)
        session = _initialize(blueprint, candidate_context=candidate_context)
        topic = next(t for t in session.topic_progress if t.topic_id == blueprint.topics[0].topic_id)
        assert "RESUME_SKILL" in blueprint.topics[0].source
        assert topic.source == TopicSource.RESUME

    def test_project_evidence_topic_reaches_resume_source(self):
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
        assert topic.source == TopicSource.RESUME

    def test_experience_evidence_topic_reaches_resume_source(self):
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
        assert topic.source == TopicSource.RESUME

    def test_mode_required_topic_reaches_behavioral_source(self):
        job_context = JobRequirementContext(
            role_title="Backend Engineer", required_skills=[], interview_duration_minutes=30,
        )
        mode = _mode(allowed_question_types=["behavioral"])
        blueprint = _build_real_blueprint(job_context, mode, _candidate_context())
        session = _initialize(blueprint, mode_id=mode.mode_id)
        behavioral_topic_bp = next(t for t in blueprint.topics if t.topic_name == "Behavioral & Situational")
        assert behavioral_topic_bp.source == "MODE_REQUIRED"
        topic = next(t for t in session.topic_progress if t.topic_id == behavioral_topic_bp.topic_id)
        assert topic.source == TopicSource.BEHAVIORAL

    def test_mixed_style_session_populates_real_source_for_every_topic(self):
        job_context = JobRequirementContext(
            role_title="Backend Engineer", required_skills=["Python"], interview_duration_minutes=60,
        )
        candidate_context = _candidate_context(
            skills=[Skill(name="Go")],
            projects=[Project(name="Inventory App", description="d", technologies=["Kubernetes"])],
        )
        mode = _mode(allowed_question_types=["behavioral"])
        blueprint = _build_real_blueprint(job_context, mode, candidate_context)
        session = _initialize(
            blueprint,
            mode_id=mode.mode_id,
            campaign_requirements=[{"skill": "Python", "criticality": "critical"}],
            candidate_context=candidate_context,
        )

        assert len(session.topic_progress) > 0
        for topic in session.topic_progress:
            assert topic.source is not None, (
                f"topic {topic.topic_id} has no source -- the bridge is still broken"
            )


class TestGapVerificationCategoryBecomesReachable:
    """Proves question_turn_planner.py's GAP_VERIFICATION routing (line ~130)
    is now reachable via the real pipeline, WITHOUT modifying its production
    logic -- this is pure observation of already-existing behavior that was
    previously dead code because topic_progress.source was always None."""

    def test_first_question_on_a_gap_topic_is_categorized_gap_verification(self):
        job_context = JobRequirementContext(
            role_title="Backend Engineer", required_skills=["Python"], interview_duration_minutes=30,
        )
        blueprint = _build_real_blueprint(job_context, _mode(), _candidate_context())
        session = _initialize(
            blueprint, campaign_requirements=[{"skill": "Python", "criticality": "critical"}],
        )
        gap_topic_id = blueprint.topics[0].topic_id
        assert session.topic_progress[0].source == TopicSource.GAP
        session.state = InterviewState.IN_PROGRESS

        plan = QuestionTurnPlanner.plan(
            session=session,
            runtime_decision=RuntimeDecision(
                current_state=InterviewState.IN_PROGRESS,
                allowed_action=RuntimeAction.ADVANCE_TOPIC,
                active_topic_id=gap_topic_id, should_complete=False,
            ),
        )
        assert plan.allowed is True
        assert plan.category == QuestionCategory.GAP_VERIFICATION

    def test_first_question_on_a_non_gap_topic_is_categorized_new(self):
        job_context = JobRequirementContext(
            role_title="Backend Engineer", required_skills=["Python"], interview_duration_minutes=30,
        )
        candidate_context = _candidate_context(skills=[Skill(name="Python")])
        blueprint = _build_real_blueprint(job_context, _mode(), candidate_context)
        session = _initialize(
            blueprint,
            campaign_requirements=[{"skill": "Python", "criticality": "critical"}],
            candidate_context=candidate_context,
        )
        topic_id = blueprint.topics[0].topic_id
        assert session.topic_progress[0].source == TopicSource.REQUIREMENT
        session.state = InterviewState.IN_PROGRESS

        plan = QuestionTurnPlanner.plan(
            session=session,
            runtime_decision=RuntimeDecision(
                current_state=InterviewState.IN_PROGRESS,
                allowed_action=RuntimeAction.ADVANCE_TOPIC,
                active_topic_id=topic_id, should_complete=False,
            ),
        )
        assert plan.allowed is True
        assert plan.category == QuestionCategory.NEW


class TestNoRegressionForDimensionBridgeAndExistingBehavior:
    """This fix must not disturb the dimension bridge (D-03 prerequisite #1)
    or existing criticality/resume_evidence behavior."""

    def test_technical_only_session_dimension_and_source_both_populated(self):
        job_context = JobRequirementContext(
            role_title="Backend Engineer", required_skills=["Python", "Docker"],
            interview_duration_minutes=30,
        )
        blueprint = _build_real_blueprint(job_context, _mode(), _candidate_context())
        session = _initialize(
            blueprint, campaign_requirements=[{"skill": "Python", "criticality": "critical"}],
        )
        from app.ai_interview.core.enums import RequirementCriticality, TopicDimension
        python_topic_bp = next(t for t in blueprint.topics if t.topic_name == "Python")
        python_progress = next(t for t in session.topic_progress if t.topic_id == python_topic_bp.topic_id)
        assert python_progress.criticality == RequirementCriticality.CRITICAL
        assert python_progress.dimension == TopicDimension.TECHNICAL
        assert python_progress.source == TopicSource.GAP
