import pytest
from pydantic import ValidationError
from datetime import datetime, timezone

from app.ai_interview.core.enums import (
    InterviewType, QuestionCategory, DifficultyLevel, RequirementCriticality,
    ResumeEvidence, InterviewEvidence, TopicDimension, TopicSource, TopicTerminalReason,
    CompletionReason
)
from app.ai_interview.schemas.strategy import (
    StrategyDefinition, MixedComposition, CampaignStrategySnapshot, RequirementCriticalityDef
)
from app.ai_interview.schemas.session import TopicProgress, InterviewSessionSchema
from app.ai_interview.question_engine.schemas import QuestionRecord
from app.ai_interview.answer_engine.schemas import EvaluationRecord
from app.ai_interview.core.enums import QuestionType
from app.ai_interview.question_engine.enums import QuestionStatus
from app.ai_interview.answer_engine.enums import CoverageSignal, FollowUpSignal
from app.ai_interview.schemas.blueprint import InterviewBlueprint, TopicBlueprint

def test_strategy_definition_valid():
    sd = StrategyDefinition(
        strategy_id="strat_1",
        name="Test",
        description="Test desc",
        applicable_interview_types=[InterviewType.TECHNICAL, InterviewType.MIXED],
        min_questions=3,
        target_questions=5,
        max_questions=7,
        max_questions_per_topic=3,
        max_followups_per_topic=2,
        strong_threshold=0.8,
        acceptable_threshold=0.6,
        weak_threshold=0.4
    )
    assert sd.min_questions == 3
    assert sd.target_questions == 5

def test_strategy_definition_invalid_budget():
    with pytest.raises(ValidationError):
        StrategyDefinition(
            strategy_id="strat_1", name="Test", description="Test",
            min_questions=5, target_questions=3, max_questions=7,
            max_questions_per_topic=3, max_followups_per_topic=2,
            strong_threshold=0.8, acceptable_threshold=0.6, weak_threshold=0.4
        )

def test_strategy_definition_invalid_thresholds():
    with pytest.raises(ValidationError):
        StrategyDefinition(
            strategy_id="strat_1", name="Test", description="Test",
            min_questions=3, target_questions=5, max_questions=7,
            max_questions_per_topic=3, max_followups_per_topic=2,
            strong_threshold=0.6, acceptable_threshold=0.8, weak_threshold=0.4
        )

def test_interview_type():
    assert InterviewType.MIXED == "mixed"
    assert InterviewType.TECHNICAL == "technical"
    assert InterviewType.RESUME_EXPERIENCE == "resume_experience"

def test_mixed_composition_valid_exact_1():
    mc = MixedComposition(technical=0.4, resume_experience=0.4, hr_behavioral=0.2, situational_case=0.0)
    assert mc.technical == 0.4
    assert mc.hr_behavioral == 0.2

def test_mixed_composition_invalid_0_9():
    with pytest.raises(ValidationError):
        MixedComposition(technical=0.4, resume_experience=0.4, hr_behavioral=0.1, situational_case=0.0)

def test_mixed_composition_invalid_1_1():
    with pytest.raises(ValidationError):
        MixedComposition(technical=0.4, resume_experience=0.4, hr_behavioral=0.3, situational_case=0.0)

def test_mixed_composition_invalid_below_10_percent():
    with pytest.raises(ValidationError) as exc:
        MixedComposition(technical=0.95, resume_experience=0.05, hr_behavioral=0.0, situational_case=0.0)
    assert "minimum weight of 0.10" in str(exc.value)

def test_mixed_composition_valid_50_50():
    mc = MixedComposition(technical=0.5, hr_behavioral=0.5)
    assert mc.technical == 0.5
    assert mc.hr_behavioral == 0.5

def test_campaign_strategy_snapshot():
    sd = StrategyDefinition(
        strategy_id="strat_1", name="Test", description="Test desc",
        min_questions=3, target_questions=5, max_questions=7,
        max_questions_per_topic=3, max_followups_per_topic=2,
        strong_threshold=0.8, acceptable_threshold=0.6, weak_threshold=0.4
    )
    snap = CampaignStrategySnapshot(snapshot_id="snap_1", definition=sd)
    assert snap.definition.strategy_id == "strat_1"
    assert isinstance(snap.snapshotted_at, datetime)

def test_requirement_criticality():
    assert RequirementCriticality.CRITICAL == "critical"
    req = RequirementCriticalityDef(skill="Python", criticality=RequirementCriticality.CRITICAL)
    assert req.criticality == "critical"

def test_evidence_separation():
    assert ResumeEvidence.STRONG == "strong"
    assert InterviewEvidence.BASIC == "basic"
    # Ensure they are different enums mapping to similar concepts but used differently
    assert ResumeEvidence.PARTIAL == "partial"
    assert InterviewEvidence.ACCEPTABLE == "acceptable"

def test_topic_state_extensions():
    tp = TopicProgress(
        topic_id="t1",
        dimension=TopicDimension.TECHNICAL,
        source=TopicSource.REQUIREMENT,
        criticality=RequirementCriticality.REQUIRED,
        resume_evidence=ResumeEvidence.PARTIAL,
        candidate_claim="I used Python for 5 years.",
        interview_evidence=InterviewEvidence.ACCEPTABLE,
        terminal_reason=TopicTerminalReason.SUFFICIENT_COVERAGE
    )
    assert tp.dimension == TopicDimension.TECHNICAL
    assert tp.resume_evidence == ResumeEvidence.PARTIAL
    assert tp.candidate_claim is not None

def test_question_record_extensions():
    qr = QuestionRecord(
        session_id="sess_1",
        turn_number=1,
        topic_id="t1",
        question_text="What is Python?",
        question_type=QuestionType.INITIAL,
        difficulty=DifficultyLevel.MEDIUM,
        category=QuestionCategory.GAP_VERIFICATION,
        dimension=TopicDimension.TECHNICAL,
        prompt_family_used="tech_gap",
        asked_at=datetime.now(timezone.utc)
    )
    assert qr.category == QuestionCategory.GAP_VERIFICATION
    assert qr.prompt_family_used == "tech_gap"

def test_evaluation_record_extensions():
    er = EvaluationRecord(
        evaluation_id="ev_1",
        question_record_id="qr_1",
        topic_id="t1",
        overall_score=0.8,
        correctness=0.9,
        coverage=0.7,
        confidence=0.85,
        followup_recommended=True,
        evidence_quality="High",
        qualitative_coverage_signal=CoverageSignal.QUALITATIVELY_COVERED,
        follow_up_signal=FollowUpSignal.NONE
    )
    assert er.correctness == 0.9
    assert er.followup_recommended is True

def test_interview_session_extensions():
    bp = InterviewBlueprint(
        blueprint_version="1",
        total_question_budget=10,
        min_questions=5,
        max_questions=15,
        emergency_max_questions=18,
        topics=[TopicBlueprint(topic_id="t1", topic_name="Python", source="req", priority=5, mandatory=True, initial_difficulty=DifficultyLevel.MEDIUM, allowed_question_types=[QuestionType.INITIAL])]
    )
    
    session = InterviewSessionSchema(
        session_id="sess_1",
        candidate_id="c_1",
        company_id="co_1",
        campaign_id="camp_1",
        mode_id="practice",
        mode_version=1,
        blueprint=bp,
        created_at=datetime.now(timezone.utc),
        interview_type=InterviewType.TECHNICAL,
        completion_reason=CompletionReason.SUFFICIENT_COVERAGE
    )
    
    assert session.interview_type == InterviewType.TECHNICAL
    assert session.completion_reason == CompletionReason.SUFFICIENT_COVERAGE

def test_backward_compatibility():
    # Attempt to load a legacy session dump
    legacy_data = {
        "session_id": "legacy_1",
        "candidate_id": "c_1",
        "company_id": "co_1",
        "campaign_id": "camp_1",
        "mode_id": "official",
        "mode_version": 1,
        "state": "created",
        "blueprint": {
            "blueprint_version": "1.0",
            "total_question_budget": 5,
            "min_questions": 3,
            "max_questions": 5,
            "emergency_max_questions": 7,
            "topics": []
        },
        "questions_asked_total": 0,
        "created_at": "2023-01-01T00:00:00Z"
    }
    
    session = InterviewSessionSchema.model_validate(legacy_data)
    assert session.session_id == "legacy_1"
    # New fields should be defaulted/None
    assert session.strategy_snapshot is None
    assert session.interview_type is None
    assert session.mixed_composition is None
    assert session.completion_reason is None
