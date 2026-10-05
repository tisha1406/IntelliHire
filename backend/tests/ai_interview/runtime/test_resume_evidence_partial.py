"""
Resume evidence: ABSENT / PARTIAL / STRONG.

Before: SessionInitializer produced only STRONG (topic name equals a listed
skill) or ABSENT, even though PARTIAL was already handled everywhere
downstream (priority weight 0.5 in ShadowPriorityCalculator, source
REQUIREMENT-not-GAP in _resolve_topic_source_from_source_codes, value passed
through to prompts and reports).

Now: a campaign-required topic that is not a listed skill but is mentioned,
as a whole word, in the resume's other text (another skill entry, experience
title/description, project name/description, certification name) is PARTIAL.
Literal and deterministic -- no stemming/synonyms/fuzzy/semantic matching.
Only ROLE_REQUIRED topics can become PARTIAL; names shorter than 3 chars,
education and interview-time claims are never consulted.

Drives the real chain: persisted resume shape -> ResumeContextBridge ->
planner -> SessionInitializer (-> shadow priority, planner, prompt).
"""
from datetime import datetime, timezone

import pytest

from app.ai_interview.transport.services.resume_context_bridge import ResumeContextBridge
from app.ai_interview.blueprint_planning.schemas import BlueprintPlanningRequest, JobRequirementContext
from app.ai_interview.blueprint_planning.topic_selector import TopicSelector
from app.ai_interview.blueprint_planning.priority_allocator import PriorityAllocator
from app.ai_interview.blueprint_planning.difficulty_planner import DifficultyPlanner
from app.ai_interview.blueprint_planning.coverage_planner import CoveragePlanner
from app.ai_interview.runtime.session_initializer import SessionInitializer
from app.ai_interview.runtime.shadow_priority_calculator import ShadowPriorityCalculator
from app.ai_interview.runtime.schemas import RuntimeDecision
from app.ai_interview.runtime.enums import RuntimeAction
from app.ai_interview.question_engine.question_engine import QuestionEngine
from app.ai_interview.question_engine.question_generator import FakeQuestionGenerator
from app.ai_interview.question_engine.question_turn_planner import QuestionTurnPlanner
from app.ai_interview.question_engine.question_request_builder import QuestionRequestBuilder
from app.ai_interview.question_engine.prompts.resolver import PromptResolver
from app.ai_interview.answer_engine.answer_engine import AnswerEngine
from app.ai_interview.answer_engine.answer_evaluator import FakeAnswerEvaluator
from app.ai_interview.answer_engine.schemas import AnswerSubmission
from app.ai_interview.orchestration.interview_turn_coordinator import InterviewTurnCoordinator
from app.ai_interview.schemas.interview_mode import InterviewModeDefinition, InterviewModeSettings
from app.ai_interview.schemas.strategy import StrategyDefinition
from app.ai_interview.core.enums import (
    InterviewModeStatus, InterviewState, InterviewType, QuestionCategory, ResumeEvidence, TopicSource,
)

RESUME = {
    "technical_skills": ["Python", "Kubernetes Administration"],
    "experience": [{
        "title": "Backend Engineer", "company": "Acme",
        "description": "Deployed services with Docker on AWS. Wrote JavaScript tooling. Led go-to-market launches.",
    }],
    "projects": [{"name": "Pipeline", "description": "CI pipeline using Jenkins"}],
    "certifications": ["Terraform Associate"],
    "education": [{"degree": "B.S. Computer Science", "institution": "State University", "year": "2019"}],
}


def _mode():
    return InterviewModeDefinition(
        mode_id="technical", name="T", description="d", version=1, status=InterviewModeStatus.PUBLISHED,
        settings=InterviewModeSettings(allowed_question_types=["initial"]), created_at=datetime.now(timezone.utc))


def _strategy(strategy_id="adaptive_depth"):
    return StrategyDefinition(
        strategy_id=strategy_id, name=strategy_id, description="d", applicable_interview_types=["technical"],
        min_questions=1, target_questions=8, max_questions=10, max_questions_per_topic=3,
        max_followups_per_topic=2, strong_threshold=0.8, acceptable_threshold=0.5, weak_threshold=0.3)


def _session(required, resume=RESUME, strategy_id="adaptive_depth", criticality="required"):
    ctx = ResumeContextBridge.build(dict(resume), "c1")
    job = JobRequirementContext(role_title="Backend Engineer", required_skills=required,
                                interview_duration_minutes=60)
    req = BlueprintPlanningRequest(candidate_context=ctx, mode_definition=_mode(), job_context=job,
                                   interview_type=InterviewType.TECHNICAL)
    topics = TopicSelector.select_topics(req)
    PriorityAllocator.allocate(topics)
    blueprint = CoveragePlanner.plan(req, topics, DifficultyPlanner.determine_initial_difficulty(req))
    session = SessionInitializer.initialize(
        blueprint=blueprint, candidate_id="c1", company_id="co", campaign_id="ca",
        mode_id="technical", mode_version=1, strategy_snapshot=_strategy(strategy_id),
        interview_type=InterviewType.TECHNICAL,
        campaign_requirements=[{"skill": s, "criticality": criticality} for s in required],
        candidate_context=ctx)
    session.state = InterviewState.IN_PROGRESS
    names = {t.topic_id: t.topic_name for t in blueprint.topics}
    return session, ctx, {names[tp.topic_id]: tp for tp in session.topic_progress}


def _plan(session, progress):
    return QuestionTurnPlanner.plan(session, RuntimeDecision(
        current_state=InterviewState.IN_PROGRESS, allowed_action=RuntimeAction.ADVANCE_TOPIC,
        active_topic_id=progress.topic_id))


REQUIRED = ["Python", "Docker", "Jenkins", "Kubernetes", "Terraform", "Java", "Go", "Rust", "Computer Science"]


class TestEvidenceStates:
    def test_listed_skill_is_strong(self):
        _, _, p = _session(REQUIRED)
        assert p["Python"].resume_evidence == ResumeEvidence.STRONG

    def test_mention_in_experience_description_is_partial(self):
        _, _, p = _session(REQUIRED)
        assert p["Docker"].resume_evidence == ResumeEvidence.PARTIAL

    def test_mention_in_project_description_is_partial(self):
        _, _, p = _session(REQUIRED)
        assert p["Jenkins"].resume_evidence == ResumeEvidence.PARTIAL

    def test_mention_inside_another_listed_skill_is_partial_not_strong(self):
        _, _, p = _session(REQUIRED)
        assert p["Kubernetes"].resume_evidence == ResumeEvidence.PARTIAL  # "Kubernetes Administration"

    def test_mention_in_certification_is_partial(self):
        _, _, p = _session(REQUIRED)
        assert p["Terraform"].resume_evidence == ResumeEvidence.PARTIAL

    def test_clearly_absent_skill_is_absent(self):
        _, _, p = _session(REQUIRED)
        assert p["Rust"].resume_evidence == ResumeEvidence.ABSENT

    def test_whole_word_only_java_is_not_found_inside_javascript(self):
        _, _, p = _session(REQUIRED)
        assert p["Java"].resume_evidence == ResumeEvidence.ABSENT

    def test_names_under_three_chars_are_never_matched_in_prose(self):
        _, _, p = _session(REQUIRED)
        assert p["Go"].resume_evidence == ResumeEvidence.ABSENT  # "go-to-market" must not count

    def test_education_is_not_consulted(self):
        _, _, p = _session(REQUIRED)
        assert p["Computer Science"].resume_evidence == ResumeEvidence.ABSENT

    def test_non_required_resume_topics_keep_their_previous_evidence(self):
        _, _, p = _session(["Python"])
        assert p["Backend Engineer"].resume_evidence == ResumeEvidence.ABSENT  # EXPERIENCE_EVIDENCE topic, unchanged


class TestDownstreamSemantics:
    def test_partial_is_not_gap_and_routes_to_new(self):
        session, _, p = _session(REQUIRED, strategy_id="fixed_coverage")
        assert p["Docker"].source == TopicSource.REQUIREMENT
        assert _plan(session, p["Docker"]).category == QuestionCategory.NEW

    def test_absent_required_skill_still_routes_to_gap(self):
        session, _, p = _session(REQUIRED, strategy_id="adaptive_depth")
        assert p["Rust"].source == TopicSource.GAP
        assert _plan(session, p["Rust"]).category == QuestionCategory.GAP_VERIFICATION

    def test_strong_stays_requirement_source(self):
        _, _, p = _session(REQUIRED)
        assert p["Python"].source == TopicSource.REQUIREMENT

    def test_priority_uses_the_existing_resume_weights(self):
        session, _, p = _session(REQUIRED)
        terms = {name: ShadowPriorityCalculator.calculate_priority(session, p[name]).breakdown["w_resume_term"]
                 for name in ("Python", "Docker", "Rust")}
        assert terms == {"Python": 1.0, "Docker": 0.5, "Rust": 0.0}

    def test_priority_order_absent_below_partial_below_strong_at_equal_criticality(self):
        session, _, p = _session(REQUIRED)
        prio = {n: ShadowPriorityCalculator.calculate_priority(session, p[n]).priority
                for n in ("Python", "Docker", "Rust")}
        assert prio["Rust"] < prio["Docker"] < prio["Python"]

    def test_prompt_shows_the_partial_state(self):
        session, ctx, p = _session(REQUIRED)
        request = QuestionRequestBuilder.build(_plan(session, p["Docker"]), ctx, _mode(), [], [])
        system_prompt, _ = PromptResolver.resolve(request)
        assert "<resume_evidence_data>\npartial\n</resume_evidence_data>" in system_prompt
        assert "Addendum: AD_TECH" in system_prompt


class TestClaimsNeverBecomeResumeEvidence:
    def test_interview_claim_does_not_change_resume_evidence(self):
        session, ctx, before = _session(REQUIRED)
        snapshot = {n: tp.resume_evidence for n, tp in before.items()}
        gen = FakeQuestionGenerator("valid")
        coord = InterviewTurnCoordinator(question_engine=QuestionEngine(generator=gen),
                                         answer_engine=AnswerEngine(evaluator=FakeAnswerEvaluator()))
        session.state = InterviewState.CREATED
        first = coord.advance_interview(session, ctx, _mode())
        coord.advance_interview(session, ctx, _mode(), answer_submission=AnswerSubmission(
            session_id=session.session_id, question_record_id=first.question.record_id,
            answer_text="excellent answer: I am a Rust and Terraform expert with ten years"))

        after = {n: tp.resume_evidence for n, tp in
                 {next(t.topic_name for t in session.blueprint.topics if t.topic_id == tp.topic_id): tp
                  for tp in session.topic_progress}.items()}
        assert after == snapshot


class TestObservedRegression:
    def test_present_python_strong_and_missing_kubernetes_absent_gap(self):
        plain = {"technical_skills": ["Python"], "experience": [], "projects": []}
        session, _, p = _session(["Python", "Kubernetes"], resume=plain)
        assert p["Python"].resume_evidence == ResumeEvidence.STRONG
        assert p["Kubernetes"].resume_evidence == ResumeEvidence.ABSENT
        assert p["Kubernetes"].source == TopicSource.GAP
