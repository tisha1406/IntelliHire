"""
GAP routing vs. the strategy/category registry.

Root cause: QuestionTurnPlanner routed EVERY TopicSource.GAP topic's first
question to QuestionCategory.GAP_VERIFICATION, but the prompt registry only
allows gap_verification for AD_TECH, AD_MIXED, GV_TECH and GV_MIXED. Once
resume skills reached the engine (so a genuinely missing required skill
became ABSENT/GAP), every other strategy/type combination (e.g. FC_TECH)
made PromptResolver raise "Category 'gap_verification' is not allowed for
combination ...", failing the first question of the topic on every retry.

Fix: a gap topic keeps GAP_VERIFICATION only where the session's registry
combination allows it; otherwise it gets NEW, which every combination allows
and which keeps the strategy's own strategy/dimension/addendum blocks. The
registry, PromptResolver, evidence algorithm and priority are untouched.

These tests drive the REAL planner/initializer/request-builder/resolver for
every combination in the registry.
"""
from datetime import datetime, timezone

import pytest

from app.ai_interview.blueprint_planning.schemas import BlueprintPlanningRequest, JobRequirementContext
from app.ai_interview.blueprint_planning.topic_selector import TopicSelector
from app.ai_interview.blueprint_planning.priority_allocator import PriorityAllocator
from app.ai_interview.blueprint_planning.difficulty_planner import DifficultyPlanner
from app.ai_interview.blueprint_planning.coverage_planner import CoveragePlanner
from app.ai_interview.runtime.session_initializer import SessionInitializer
from app.ai_interview.runtime.schemas import RuntimeDecision
from app.ai_interview.runtime.enums import RuntimeAction
from app.ai_interview.question_engine.question_turn_planner import QuestionTurnPlanner
from app.ai_interview.question_engine.question_request_builder import QuestionRequestBuilder
from app.ai_interview.question_engine.prompts.resolver import PromptResolver
from app.ai_interview.question_engine.prompts.registry import COMBINATION_REGISTRY
from app.ai_interview.schemas.interview_mode import InterviewModeDefinition, InterviewModeSettings
from app.ai_interview.schemas.strategy import StrategyDefinition, MixedComposition
from app.ai_interview.schemas.resume import StructuredResume, Skill
from app.ai_interview.resume_processing.schemas import CandidateInterviewContext
from app.ai_interview.resume_processing.enums import ExtractionQualityStatus
from app.ai_interview.core.enums import (
    InterviewModeStatus, InterviewState, InterviewType, QuestionCategory, TopicSource, ResumeEvidence,
)

CATEGORY_ALLOWS_GAP = {"adaptive_depth", "gap_verification"}  # strategies whose combos allow it


def _mode():
    return InterviewModeDefinition(
        mode_id="technical", name="T", description="d", version=1, status=InterviewModeStatus.PUBLISHED,
        settings=InterviewModeSettings(allowed_question_types=["initial"]), created_at=datetime.now(timezone.utc),
    )


def _context():
    return CandidateInterviewContext(
        candidate_id="c1", structured_resume=StructuredResume(skills=[Skill(name="Python")]),
        extraction_metadata={"source_type": "pdf", "extractor_name": "t", "extractor_version": "1",
                             "character_count": 1, "detected_sections": [], "warning_count": 0,
                             "processing_duration_ms": 1.0},
        quality_status=ExtractionQualityStatus.USABLE, warnings=[],
    )


def _strategy(strategy_id, interview_type):
    return StrategyDefinition(
        strategy_id=strategy_id, name=strategy_id, description="d",
        applicable_interview_types=[interview_type], min_questions=1, target_questions=5,
        max_questions=6, max_questions_per_topic=2, max_followups_per_topic=1,
        strong_threshold=0.8, acceptable_threshold=0.5, weak_threshold=0.3,
    )


def _session(strategy_id, interview_type_value):
    """Required skills: Python (in the resume -> STRONG) and Kubernetes (not
    in the resume -> ABSENT -> TopicSource.GAP)."""
    itype = InterviewType(interview_type_value)
    comp = (MixedComposition(technical=0.5, resume_experience=0.5, hr_behavioral=0.0, situational_case=0.0)
            if itype == InterviewType.MIXED else None)
    ctx = _context()
    job = JobRequirementContext(role_title="Backend Engineer", required_skills=["Python", "Kubernetes"],
                                interview_duration_minutes=30)
    request = BlueprintPlanningRequest(candidate_context=ctx, mode_definition=_mode(), job_context=job,
                                       interview_type=itype, mixed_composition=comp)
    topics = TopicSelector.select_topics(request)
    PriorityAllocator.allocate(topics)
    blueprint = CoveragePlanner.plan(request, topics, DifficultyPlanner.determine_initial_difficulty(request))
    session = SessionInitializer.initialize(
        blueprint=blueprint, candidate_id="c1", company_id="co", campaign_id="ca",
        mode_id="technical", mode_version=1,
        strategy_snapshot=_strategy(strategy_id, interview_type_value) if strategy_id else None,
        interview_type=itype, mixed_composition=comp,
        campaign_requirements=[{"skill": "Python", "criticality": "critical"},
                               {"skill": "Kubernetes", "criticality": "required"}],
        candidate_context=ctx,
    )
    session.state = InterviewState.IN_PROGRESS
    names = {t.topic_id: t.topic_name for t in blueprint.topics}
    return session, {names[tp.topic_id]: tp for tp in session.topic_progress}


def _plan_for(session, progress):
    return QuestionTurnPlanner.plan(session, RuntimeDecision(
        current_state=InterviewState.IN_PROGRESS, allowed_action=RuntimeAction.ADVANCE_TOPIC,
        active_topic_id=progress.topic_id,
    ))


REGISTRY_COMBOS = [(c.strategy_id, c.interview_type) for c in COMBINATION_REGISTRY]


@pytest.mark.parametrize("strategy_id,interview_type", REGISTRY_COMBOS)
def test_gap_topic_always_reaches_a_registry_valid_category_the_resolver_accepts(strategy_id, interview_type):
    session, progress = _session(strategy_id, interview_type)
    assert progress["Kubernetes"].source == TopicSource.GAP
    assert progress["Kubernetes"].resume_evidence == ResumeEvidence.ABSENT

    plan = _plan_for(session, progress["Kubernetes"])

    combo = next(c for c in COMBINATION_REGISTRY
                 if c.strategy_id == strategy_id and c.interview_type == interview_type)
    assert plan.allowed is True
    assert plan.category.value in combo.allowed_categories
    request = QuestionRequestBuilder.build(plan, _context(), _mode(), [], [])
    PromptResolver.resolve(request)  # must not raise


@pytest.mark.parametrize("strategy_id,interview_type", REGISTRY_COMBOS)
def test_gap_verification_retained_exactly_where_the_registry_allows_it(strategy_id, interview_type):
    session, progress = _session(strategy_id, interview_type)
    plan = _plan_for(session, progress["Kubernetes"])

    if strategy_id in CATEGORY_ALLOWS_GAP:
        assert plan.category == QuestionCategory.GAP_VERIFICATION
    else:
        assert plan.category == QuestionCategory.NEW


@pytest.mark.parametrize("strategy_id,interview_type", [
    ("fixed_coverage", "technical"), ("critical_skills", "technical"), ("breadth", "technical"),
    ("behavioral_adaptive", "hr_behavioral"), ("fixed_coverage", "mixed"), ("breadth", "mixed"),
])
def test_fallback_keeps_the_strategys_own_prompt_blocks(strategy_id, interview_type):
    """The fallback changes only the category block -- the strategy block and
    addendum still identify the original strategy/combination."""
    session, progress = _session(strategy_id, interview_type)
    plan = _plan_for(session, progress["Kubernetes"])
    system_prompt, _ = PromptResolver.resolve(QuestionRequestBuilder.build(plan, _context(), _mode(), [], []))

    combo = next(c for c in COMBINATION_REGISTRY
                 if c.strategy_id == strategy_id and c.interview_type == interview_type)
    assert f"Addendum: {combo.combination_id}" in system_prompt
    assert "Category: NEW" in system_prompt
    assert "GAP_VERIFICATION" not in system_prompt


def test_adaptive_depth_gap_behaviour_is_unchanged():
    session, progress = _session("adaptive_depth", "technical")
    plan = _plan_for(session, progress["Kubernetes"])
    assert plan.category == QuestionCategory.GAP_VERIFICATION
    system_prompt, _ = PromptResolver.resolve(QuestionRequestBuilder.build(plan, _context(), _mode(), [], []))
    assert "Category: GAP_VERIFICATION" in system_prompt


@pytest.mark.parametrize("strategy_id,interview_type", REGISTRY_COMBOS)
def test_non_gap_topic_is_unaffected(strategy_id, interview_type):
    session, progress = _session(strategy_id, interview_type)
    assert progress["Python"].source == TopicSource.REQUIREMENT
    plan = _plan_for(session, progress["Python"])
    assert plan.category == QuestionCategory.NEW


def test_session_without_a_strategy_snapshot_keeps_gap_verification():
    """Legacy/Practice sessions never reach registry validation -- existing
    behaviour (covered by test_source_bridge.py) must be preserved."""
    session, progress = _session(None, "technical")
    assert session.strategy_snapshot is None
    plan = _plan_for(session, progress["Kubernetes"])
    assert plan.category == QuestionCategory.GAP_VERIFICATION


def test_unrecognised_combination_is_left_for_the_resolver_to_report():
    session, progress = _session("some_unregistered_strategy", "technical")
    plan = _plan_for(session, progress["Kubernetes"])
    assert plan.category == QuestionCategory.GAP_VERIFICATION
