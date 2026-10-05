"""
D-04 regression tests: threading TopicBlueprint.scenario_context (D-03)
through QuestionTurnPlanner -> QuestionTurnPlan -> QuestionRequestBuilder ->
PromptResolver.

Before this fix, QuestionTurnPlanner hardcoded `scenario_context=None` at
both QuestionTurnPlan construction sites (the allowed-plan path and the
denied-plan path), so the real value already snapshotted onto TopicBlueprint
by D-03 never reached question generation -- the situational prompt
templates (ENV_SITUATIONAL etc.) always rendered "NOT_PROVIDED".

The fix only reads `topic_bp.scenario_context` (the same TopicBlueprint
instance already supplying topic_name/difficulty/etc. to the plan) -- no new
field, no new lookup, no Mongo/LLM access during planning.
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
from app.ai_interview.runtime.session_initializer import SessionInitializer
from app.ai_interview.question_engine.question_turn_planner import QuestionTurnPlanner
from app.ai_interview.question_engine.question_request_builder import QuestionRequestBuilder
from app.ai_interview.question_engine.prompts.resolver import PromptResolver
from app.ai_interview.question_engine.schemas import QuestionGenerationRequest
from app.ai_interview.runtime.schemas import RuntimeDecision
from app.ai_interview.runtime.enums import RuntimeAction
from app.ai_interview.schemas.interview_mode import (
    InterviewModeDefinition, InterviewModeSettings,
)
from app.ai_interview.schemas.strategy import MixedComposition
from app.ai_interview.core.enums import (
    InterviewModeStatus, InterviewType, TopicDimension, TopicSource,
    DifficultyLevel, QuestionCategory, InterviewState, QuestionType,
)
from app.ai_interview.resume_processing.schemas import CandidateInterviewContext
from app.ai_interview.schemas.resume import StructuredResume, Skill
from app.ai_interview.resume_processing.enums import ExtractionQualityStatus


SCENARIO = Scenario(
    scenario_id="sit_test_d04_001",
    role_or_domain="backend engineer",
    topic_name="Handling a Production Outage During a Launch",
    scenario_context="SENTINEL_SCENARIO_CONTEXT: a detailed outage case study.",
    difficulty=DifficultyLevel.MEDIUM,
    is_active=True,
)


def _mode(allowed_question_types=None, mode_id="technical"):
    return InterviewModeDefinition(
        mode_id=mode_id, name="Technical", description="d", version=1,
        status=InterviewModeStatus.PUBLISHED,
        settings=InterviewModeSettings(allowed_question_types=allowed_question_types or ["initial"]),
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


def _job_context(required_skills=None):
    return JobRequirementContext(
        role_title="Backend Engineer", required_skills=required_skills or [],
        interview_duration_minutes=30,
    )


def _plan_blueprint(job_context, mode, candidate_context,
                     interview_type=None, mixed_composition=None, selected_scenario=None):
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


def _decision(topic_id):
    return RuntimeDecision(
        current_state=InterviewState.IN_PROGRESS,
        allowed_action=RuntimeAction.ADVANCE_TOPIC,
        active_topic_id=topic_id, should_complete=False,
    )


# ── A. Pure situational interview ───────────────────────────────────────────

class TestPureSituationalInterview:
    def test_blueprint_has_scenario_context(self):
        blueprint = _plan_blueprint(
            _job_context(), _mode(), _candidate_context(),
            interview_type=InterviewType.SITUATIONAL_CASE, selected_scenario=SCENARIO,
        )
        topic_bp = next(t for t in blueprint.topics if t.scenario_id == SCENARIO.scenario_id)
        assert topic_bp.scenario_context == SCENARIO.scenario_context

    def test_question_turn_planner_receives_and_forwards_it(self):
        blueprint = _plan_blueprint(
            _job_context(), _mode(), _candidate_context(),
            interview_type=InterviewType.SITUATIONAL_CASE, selected_scenario=SCENARIO,
        )
        session = _initialize(blueprint, interview_type=InterviewType.SITUATIONAL_CASE)
        session.state = InterviewState.IN_PROGRESS
        topic_bp = next(t for t in blueprint.topics if t.scenario_id == SCENARIO.scenario_id)

        plan = QuestionTurnPlanner.plan(session, _decision(topic_bp.topic_id))

        assert plan.allowed is True
        assert plan.scenario_context == SCENARIO.scenario_context == topic_bp.scenario_context

    def test_no_database_lookup_occurs_during_planning(self):
        """QuestionTurnPlanner.plan is a synchronous staticmethod with no
        repository import -- it is architecturally incapable of querying
        Mongo. This asserts that invariant directly against the source,
        the same static-scan pattern used elsewhere in this codebase
        (e.g. test_interview_result_service.py's no-LLM-call test)."""
        import inspect
        source = inspect.getsource(QuestionTurnPlanner)
        assert "ScenarioRepository" not in source
        assert "scenario_repository" not in source
        assert "await" not in source  # confirms the method stays fully synchronous


# ── B. Mixed interview ───────────────────────────────────────────────────────

class TestMixedInterview:
    def test_situational_topic_receives_context_non_situational_receive_none(self):
        comp = MixedComposition(technical=0.5, resume_experience=0.0, hr_behavioral=0.0, situational_case=0.5)
        blueprint = _plan_blueprint(
            _job_context(required_skills=["Python"]), _mode(), _candidate_context(),
            interview_type=InterviewType.MIXED, mixed_composition=comp, selected_scenario=SCENARIO,
        )
        session = _initialize(
            blueprint, campaign_requirements=[{"skill": "Python", "criticality": "critical"}],
            interview_type=InterviewType.MIXED, mixed_composition=comp,
        )
        session.state = InterviewState.IN_PROGRESS

        python_bp = next(t for t in blueprint.topics if t.topic_name == "Python")
        situational_bp = next(t for t in blueprint.topics if t.scenario_id == SCENARIO.scenario_id)

        python_plan = QuestionTurnPlanner.plan(session, _decision(python_bp.topic_id))
        situational_plan = QuestionTurnPlanner.plan(session, _decision(situational_bp.topic_id))

        assert python_plan.scenario_context is None
        assert situational_plan.scenario_context == SCENARIO.scenario_context


# ── C. Non-situational regression ───────────────────────────────────────────

class TestNonSituationalRegression:
    def test_technical_topic_scenario_context_is_none(self):
        blueprint = _plan_blueprint(
            _job_context(required_skills=["Python"]), _mode(), _candidate_context(),
        )
        session = _initialize(
            blueprint, campaign_requirements=[{"skill": "Python", "criticality": "critical"}],
        )
        session.state = InterviewState.IN_PROGRESS
        topic_bp = next(t for t in blueprint.topics if t.topic_name == "Python")
        plan = QuestionTurnPlanner.plan(session, _decision(topic_bp.topic_id))
        assert plan.dimension == TopicDimension.TECHNICAL
        assert plan.scenario_context is None

    def test_resume_topic_scenario_context_is_none(self):
        blueprint = _plan_blueprint(
            _job_context(), _mode(), _candidate_context(skills=[Skill(name="Go")]),
        )
        session = _initialize(blueprint, candidate_context=_candidate_context(skills=[Skill(name="Go")]))
        session.state = InterviewState.IN_PROGRESS
        topic_bp = next(t for t in blueprint.topics if t.topic_name == "Go")
        plan = QuestionTurnPlanner.plan(session, _decision(topic_bp.topic_id))
        assert plan.scenario_context is None

    def test_behavioral_topic_scenario_context_is_none(self):
        mode = _mode(allowed_question_types=["behavioral"])
        blueprint = _plan_blueprint(_job_context(), mode, _candidate_context())
        session = _initialize(blueprint, mode_id=mode.mode_id)
        session.state = InterviewState.IN_PROGRESS
        topic_bp = next(t for t in blueprint.topics if t.topic_name == "Behavioral & Situational")
        plan = QuestionTurnPlanner.plan(session, _decision(topic_bp.topic_id))
        assert plan.dimension == TopicDimension.BEHAVIORAL
        assert plan.scenario_context is None

    def test_gap_verification_topic_scenario_context_is_none(self):
        """ROLE_REQUIRED + ResumeEvidence.ABSENT -> TopicSource.GAP ->
        QuestionCategory.GAP_VERIFICATION -- must continue working unchanged
        and must never pick up a scenario_context (GAP has nothing to do
        with the situational scenario bank)."""
        blueprint = _plan_blueprint(
            _job_context(required_skills=["Python"]), _mode(), _candidate_context(),
        )
        session = _initialize(
            blueprint, campaign_requirements=[{"skill": "Python", "criticality": "critical"}],
        )
        session.state = InterviewState.IN_PROGRESS
        topic_bp = next(t for t in blueprint.topics if t.topic_name == "Python")

        assert session.topic_progress[0].source == TopicSource.GAP  # unchanged D-03-prereq behavior

        plan = QuestionTurnPlanner.plan(session, _decision(topic_bp.topic_id))

        assert plan.allowed is True
        assert plan.category == QuestionCategory.GAP_VERIFICATION
        assert plan.scenario_context is None

    def test_denied_plan_path_also_returns_none_for_non_situational_topic(self):
        """The _deny() construction site is the second (previously also
        hardcoded) QuestionTurnPlan build path."""
        blueprint = _plan_blueprint(
            _job_context(required_skills=["Python"]), _mode(), _candidate_context(),
        )
        session = _initialize(
            blueprint, campaign_requirements=[{"skill": "Python", "criticality": "critical"}],
        )
        session.state = InterviewState.CREATED  # forces a denial (not IN_PROGRESS)
        topic_bp = next(t for t in blueprint.topics if t.topic_name == "Python")

        plan = QuestionTurnPlanner.plan(session, _decision(topic_bp.topic_id))

        assert plan.allowed is False
        assert plan.scenario_context is None


# ── D. Prompt-generation integration ────────────────────────────────────────

class TestPromptGenerationIntegration:
    def test_request_builder_forwards_scenario_context_into_generation_request(self):
        blueprint = _plan_blueprint(
            _job_context(), _mode(), _candidate_context(),
            interview_type=InterviewType.SITUATIONAL_CASE, selected_scenario=SCENARIO,
        )
        session = _initialize(blueprint, interview_type=InterviewType.SITUATIONAL_CASE)
        session.state = InterviewState.IN_PROGRESS
        topic_bp = next(t for t in blueprint.topics if t.scenario_id == SCENARIO.scenario_id)

        plan = QuestionTurnPlanner.plan(session, _decision(topic_bp.topic_id))
        request = QuestionRequestBuilder.build(
            plan=plan,
            candidate_context=_candidate_context(),
            mode=_mode(),
            question_history=[],
            evaluation_history=[],
        )
        assert request.scenario_context == SCENARIO.scenario_context

    def test_prompt_resolver_renders_the_real_scenario_context_for_pure_situational(self):
        """FC_SIT combination (fixed_coverage + situational_case). We check
        the structured input (request.scenario_context) and that the
        rendered system prompt contains the real context string rather than
        the "NOT_PROVIDED" placeholder -- not a fragile full-prompt match."""
        request = QuestionGenerationRequest(
            session_id="s1", turn_number=1, topic_id="t1",
            topic_name=SCENARIO.topic_name,
            interview_type=InterviewType.SITUATIONAL_CASE,
            strategy="Fixed Coverage", strategy_id="fixed_coverage",
            category=QuestionCategory.NEW,
            scenario_context=SCENARIO.scenario_context,
            difficulty=DifficultyLevel.MEDIUM,
            allowed_question_types=[QuestionType.INITIAL],
            selected_question_type=QuestionType.INITIAL,
            question_number=1,
            max_questions_for_topic=2,
        )
        system_prompt, _ = PromptResolver.resolve(request)
        expected_block = "<scenario_context_data>\n" + SCENARIO.scenario_context + "\n</scenario_context_data>"
        assert expected_block in system_prompt

    def test_prompt_resolver_renders_not_provided_when_scenario_context_is_none(self):
        """Sanity check on the other side of the fix: a situational-dimension
        prompt with no scenario_context (e.g. no scenario was available)
        still renders cleanly with the existing NOT_PROVIDED placeholder --
        proves D-04 didn't break that pre-existing fallback."""
        request = QuestionGenerationRequest(
            session_id="s1", turn_number=1, topic_id="t1", topic_name="Some Topic",
            interview_type=InterviewType.SITUATIONAL_CASE,
            strategy="Fixed Coverage", strategy_id="fixed_coverage",
            category=QuestionCategory.NEW,
            scenario_context=None,
            difficulty=DifficultyLevel.MEDIUM,
            allowed_question_types=[QuestionType.INITIAL],
            selected_question_type=QuestionType.INITIAL,
            question_number=1,
            max_questions_for_topic=2,
        )
        system_prompt, _ = PromptResolver.resolve(request)
        not_provided_block = "<scenario_context_data>\nNOT_PROVIDED\n</scenario_context_data>"
        assert not_provided_block in system_prompt


# ── E. Snapshot / immutability behavior ─────────────────────────────────────

class TestSnapshotImmutability:
    def test_planning_uses_the_blueprints_stored_scenario_not_a_fresh_lookup(self, monkeypatch):
        """Even if ScenarioRepository would now return a different scenario
        (or raise), QuestionTurnPlanner must keep using the blueprint's
        already-snapshotted value -- it never calls the repository at all."""
        blueprint = _plan_blueprint(
            _job_context(), _mode(), _candidate_context(),
            interview_type=InterviewType.SITUATIONAL_CASE, selected_scenario=SCENARIO,
        )
        session = _initialize(blueprint, interview_type=InterviewType.SITUATIONAL_CASE)
        session.state = InterviewState.IN_PROGRESS
        topic_bp = next(t for t in blueprint.topics if t.scenario_id == SCENARIO.scenario_id)

        async def _boom(*args, **kwargs):
            raise AssertionError("ScenarioRepository must never be queried during question planning")

        from app.repositories.scenario_repository import ScenarioRepository
        monkeypatch.setattr(ScenarioRepository, "select_scenario_for_role", _boom)
        monkeypatch.setattr(ScenarioRepository, "get_active_for_role", _boom)

        plan = QuestionTurnPlanner.plan(session, _decision(topic_bp.topic_id))

        assert plan.scenario_context == SCENARIO.scenario_context
