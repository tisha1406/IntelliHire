"""
D-03 tests: situational scenario bank + deterministic topic selection.

Exercises the REAL TopicSelector -> PriorityAllocator -> CoveragePlanner ->
SessionInitializer pipeline (not hand-constructed TopicProgress fixtures),
with an in-memory `selected_scenario` standing in for the already-fetched
ScenarioRepository result (repository I/O itself is covered separately in
tests/integration/test_scenario_repository.py) -- this mirrors how
candidate_context/job_context are already pre-fetched data passed into the
synchronous blueprint_planning pipeline.
"""
from datetime import datetime, timezone

import pytest

from app.ai_interview.blueprint_planning.topic_selector import TopicSelector
from app.ai_interview.blueprint_planning.coverage_planner import CoveragePlanner
from app.ai_interview.blueprint_planning.priority_allocator import PriorityAllocator
from app.ai_interview.blueprint_planning.difficulty_planner import DifficultyPlanner
from app.ai_interview.blueprint_planning.schemas import (
    BlueprintPlanningRequest, JobRequirementContext,
)
from app.ai_interview.blueprint_planning.scenario_schemas import Scenario
from app.ai_interview.blueprint_planning.enums import TopicSourceCode
from app.ai_interview.runtime.session_initializer import SessionInitializer
from app.ai_interview.schemas.interview_mode import (
    InterviewModeDefinition, InterviewModeSettings,
)
from app.ai_interview.schemas.strategy import MixedComposition
from app.ai_interview.core.enums import (
    InterviewModeStatus, TopicDimension, TopicSource, InterviewType, DifficultyLevel,
)
from app.ai_interview.resume_processing.schemas import CandidateInterviewContext
from app.ai_interview.schemas.resume import StructuredResume, Skill
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


def _candidate_context(skills=None):
    return CandidateInterviewContext(
        candidate_id="cand1",
        structured_resume=StructuredResume(skills=skills or []),
        extraction_metadata={
            "source_type": "pdf", "extractor_name": "test", "extractor_version": "1.0",
            "character_count": 100, "detected_sections": [], "warning_count": 0,
            "processing_duration_ms": 1.0,
        },
        quality_status=ExtractionQualityStatus.USABLE,
        warnings=[],
    )


SCENARIO = Scenario(
    scenario_id="sit_test_001",
    role_or_domain="backend engineer",
    topic_name="Handling a Production Outage During a Launch",
    scenario_context="A detailed situational case about an outage during launch.",
    difficulty=DifficultyLevel.MEDIUM,
    is_active=True,
)


def _plan_blueprint(
    job_context, mode, candidate_context,
    interview_type=None, mixed_composition=None, selected_scenario=None,
):
    """Runs the REAL blueprint_planning pipeline end to end."""
    request = BlueprintPlanningRequest(
        candidate_context=candidate_context, mode_definition=mode, job_context=job_context,
        interview_type=interview_type, mixed_composition=mixed_composition,
        selected_scenario=selected_scenario,
    )
    topics = TopicSelector.select_topics(request)
    PriorityAllocator.allocate(topics)
    initial_difficulty = DifficultyPlanner.determine_initial_difficulty(request)
    return CoveragePlanner.plan(request, topics, initial_difficulty)


def _initialize(blueprint, mode_id="technical", campaign_requirements=None,
                 candidate_context=None, interview_type=None, mixed_composition=None):
    return SessionInitializer.initialize(
        blueprint=blueprint, candidate_id="cand1", company_id="co1", campaign_id="cam1",
        mode_id=mode_id, mode_version=1,
        campaign_requirements=campaign_requirements, candidate_context=candidate_context,
        interview_type=interview_type, mixed_composition=mixed_composition,
    )


def _job_context(required_skills=None):
    return JobRequirementContext(
        role_title="Backend Engineer", required_skills=required_skills or [],
        interview_duration_minutes=30,
    )


class TestPureSituationalCase:
    def test_produces_a_situational_topic_when_scenario_available(self):
        blueprint = _plan_blueprint(
            _job_context(), _mode(), _candidate_context(),
            interview_type=InterviewType.SITUATIONAL_CASE,
            selected_scenario=SCENARIO,
        )
        situational_topics = [t for t in blueprint.topics if "SITUATIONAL_SCENARIO" in t.source]
        assert len(situational_topics) == 1
        topic = situational_topics[0]
        assert topic.topic_name == SCENARIO.topic_name
        assert topic.scenario_id == SCENARIO.scenario_id
        assert topic.scenario_context == SCENARIO.scenario_context

    def test_situational_topic_reaches_situational_dimension_at_runtime(self):
        blueprint = _plan_blueprint(
            _job_context(), _mode(), _candidate_context(),
            interview_type=InterviewType.SITUATIONAL_CASE,
            selected_scenario=SCENARIO,
        )
        session = _initialize(blueprint, interview_type=InterviewType.SITUATIONAL_CASE)
        situational_topic_bp = next(t for t in blueprint.topics if t.scenario_id == SCENARIO.scenario_id)
        progress = next(t for t in session.topic_progress if t.topic_id == situational_topic_bp.topic_id)
        assert progress.dimension == TopicDimension.SITUATIONAL
        # No core.enums.TopicSource value represents "situational" and
        # nothing consumes one -- see session_initializer.py's
        # _resolve_topic_source_from_source_codes module comment.
        assert progress.source is None

    def test_scenario_survives_into_runtime_blueprint_unmodified(self):
        """TopicBlueprint is part of the immutable session.blueprint, so the
        scenario snapshot taken at planning time must still be reachable at
        runtime exactly as planned (D-04 will read it from here)."""
        blueprint = _plan_blueprint(
            _job_context(), _mode(), _candidate_context(),
            interview_type=InterviewType.SITUATIONAL_CASE,
            selected_scenario=SCENARIO,
        )
        session = _initialize(blueprint, interview_type=InterviewType.SITUATIONAL_CASE)
        situational_topic_bp = next(t for t in session.blueprint.topics if t.scenario_id == SCENARIO.scenario_id)
        assert situational_topic_bp.scenario_context == SCENARIO.scenario_context

    def test_repeated_planning_with_same_inputs_is_deterministic(self):
        blueprint1 = _plan_blueprint(
            _job_context(), _mode(), _candidate_context(),
            interview_type=InterviewType.SITUATIONAL_CASE, selected_scenario=SCENARIO,
        )
        blueprint2 = _plan_blueprint(
            _job_context(), _mode(), _candidate_context(),
            interview_type=InterviewType.SITUATIONAL_CASE, selected_scenario=SCENARIO,
        )
        names1 = sorted(t.topic_name for t in blueprint1.topics)
        names2 = sorted(t.topic_name for t in blueprint2.topics)
        assert names1 == names2
        scenario_ctx_1 = next(t.scenario_context for t in blueprint1.topics if t.scenario_id)
        scenario_ctx_2 = next(t.scenario_context for t in blueprint2.topics if t.scenario_id)
        assert scenario_ctx_1 == scenario_ctx_2 == SCENARIO.scenario_context

    def test_situational_topic_is_mandatory_and_survives_truncation(self):
        """Mirrors MODE_REQUIRED's existing guarantee: a deliberately
        requested situational topic must not be silently dropped."""
        blueprint = _plan_blueprint(
            _job_context(), _mode(), _candidate_context(),
            interview_type=InterviewType.SITUATIONAL_CASE, selected_scenario=SCENARIO,
        )
        situational_topic = next(t for t in blueprint.topics if t.scenario_id == SCENARIO.scenario_id)
        assert situational_topic.mandatory is True


class TestMixedInterviews:
    def test_situational_dimension_produced_when_composition_requests_it(self):
        comp = MixedComposition(
            technical=0.5, resume_experience=0.2, hr_behavioral=0.0, situational_case=0.3,
        )
        blueprint = _plan_blueprint(
            _job_context(required_skills=["Python"]), _mode(), _candidate_context(skills=[Skill(name="Go")]),
            interview_type=InterviewType.MIXED, mixed_composition=comp, selected_scenario=SCENARIO,
        )
        situational_topics = [t for t in blueprint.topics if t.scenario_id == SCENARIO.scenario_id]
        assert len(situational_topics) == 1

        session = _initialize(
            blueprint, campaign_requirements=[{"skill": "Python", "criticality": "critical"}],
            candidate_context=_candidate_context(skills=[Skill(name="Go")]),
            interview_type=InterviewType.MIXED, mixed_composition=comp,
        )
        # Existing dimensions remain intact (regression within this same test).
        python_progress = next(t for t in session.topic_progress if t.criticality is not None)
        assert python_progress.dimension == TopicDimension.TECHNICAL
        go_progress = next(
            t for t in session.topic_progress
            if t.topic_id in {tb.topic_id for tb in blueprint.topics if tb.topic_name == "Go"}
        )
        assert go_progress.dimension == TopicDimension.TECHNICAL

        situational_bp = situational_topics[0]
        situational_progress = next(t for t in session.topic_progress if t.topic_id == situational_bp.topic_id)
        assert situational_progress.dimension == TopicDimension.SITUATIONAL

    def test_mixed_composition_math_is_not_rewritten(self):
        """ShadowPriorityCalculator (untouched by D-03) must still read
        mixed_composition.situational_case directly for its composition
        score -- this just proves the dimension it needs is now reachable."""
        from app.ai_interview.runtime.shadow_priority_calculator import ShadowPriorityCalculator

        comp = MixedComposition(
            technical=0.5, resume_experience=0.0, hr_behavioral=0.0, situational_case=0.5,
        )
        blueprint = _plan_blueprint(
            _job_context(required_skills=["Python"]), _mode(), _candidate_context(),
            interview_type=InterviewType.MIXED, mixed_composition=comp, selected_scenario=SCENARIO,
        )
        session = _initialize(
            blueprint,
            campaign_requirements=[{"skill": "Python", "criticality": "critical"}],
            interview_type=InterviewType.MIXED, mixed_composition=comp,
        )
        situational_bp = next(t for t in blueprint.topics if t.scenario_id == SCENARIO.scenario_id)
        situational_progress = next(t for t in session.topic_progress if t.topic_id == situational_bp.topic_id)

        result = ShadowPriorityCalculator.calculate_priority(session, situational_progress)
        assert result.composition_score == 0.5  # comp.situational_case, read verbatim, formula untouched

    def test_no_situational_weight_means_no_situational_topic_even_with_scenario_available(self):
        comp = MixedComposition(
            technical=0.6, resume_experience=0.4, hr_behavioral=0.0, situational_case=0.0,
        )
        blueprint = _plan_blueprint(
            _job_context(required_skills=["Python"]), _mode(), _candidate_context(),
            interview_type=InterviewType.MIXED, mixed_composition=comp, selected_scenario=SCENARIO,
        )
        assert not any(t.scenario_id for t in blueprint.topics)


class TestNoScenarioAvailable:
    def test_situational_case_with_no_scenario_does_not_fabricate_one(self):
        blueprint = _plan_blueprint(
            _job_context(required_skills=["Python"]), _mode(), _candidate_context(),
            interview_type=InterviewType.SITUATIONAL_CASE, selected_scenario=None,
        )
        assert not any(t.scenario_id for t in blueprint.topics)
        # The rest of the (non-situational) pipeline still works normally.
        assert len(blueprint.topics) > 0

    def test_unrelated_interview_types_unaffected_by_scenario_absence(self):
        blueprint = _plan_blueprint(
            _job_context(required_skills=["Python", "Docker"]), _mode(), _candidate_context(),
            interview_type=InterviewType.TECHNICAL, selected_scenario=None,
        )
        assert len(blueprint.topics) == 2
        assert not any(t.scenario_id for t in blueprint.topics)


class TestRegressionExistingBehaviorUnchanged:
    def test_technical_only_plan_unaffected_by_new_optional_fields(self):
        """A caller that never sets interview_type/mixed_composition/
        selected_scenario (all default to None) must behave exactly as
        before D-03."""
        blueprint = _plan_blueprint(
            _job_context(required_skills=["Python"]), _mode(), _candidate_context(skills=[Skill(name="Go")]),
        )
        assert not any(t.scenario_id for t in blueprint.topics)
        names = {t.topic_name for t in blueprint.topics}
        assert names == {"Python", "Go"}

    def test_role_required_gap_and_dimension_bridges_still_work_alongside_situational(self):
        comp = MixedComposition(
            technical=0.5, resume_experience=0.0, hr_behavioral=0.0, situational_case=0.5,
        )
        blueprint = _plan_blueprint(
            _job_context(required_skills=["Python"]), _mode(), _candidate_context(),
            interview_type=InterviewType.MIXED, mixed_composition=comp, selected_scenario=SCENARIO,
        )
        session = _initialize(
            blueprint,
            campaign_requirements=[{"skill": "Python", "criticality": "critical"}],
            interview_type=InterviewType.MIXED, mixed_composition=comp,
        )
        python_bp = next(t for t in blueprint.topics if t.topic_name == "Python")
        python_progress = next(t for t in session.topic_progress if t.topic_id == python_bp.topic_id)
        # ROLE_REQUIRED + ResumeEvidence.ABSENT -> GAP, unaffected by the new
        # SITUATIONAL_SCENARIO code's addition to the shared precedence list.
        assert python_progress.source == TopicSource.GAP
        assert python_progress.dimension == TopicDimension.TECHNICAL

    def test_mode_required_behavioral_topic_still_produced_alongside_situational(self):
        comp = MixedComposition(
            technical=0.0, resume_experience=0.0, hr_behavioral=0.5, situational_case=0.5,
        )
        mode = _mode(allowed_question_types=["behavioral"])
        blueprint = _plan_blueprint(
            _job_context(), mode, _candidate_context(),
            interview_type=InterviewType.MIXED, mixed_composition=comp, selected_scenario=SCENARIO,
        )
        topic_names = {t.topic_name for t in blueprint.topics}
        assert "Behavioral & Situational" in topic_names
        assert SCENARIO.topic_name in topic_names
