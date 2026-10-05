import pytest
from app.ai_interview.runtime.session_initializer import SessionInitializer
from app.ai_interview.schemas.blueprint import InterviewBlueprint, TopicBlueprint
from app.ai_interview.core.enums import (
    DifficultyLevel, QuestionType, InterviewType, RequirementCriticality, 
    TopicDimension, TopicSource, ResumeEvidence
)
from app.ai_interview.schemas.strategy import StrategyDefinition, MixedComposition
from app.ai_interview.resume_processing.schemas import CandidateInterviewContext
from app.ai_interview.schemas.resume import StructuredResume, Skill
from app.ai_interview.resume_processing.enums import ExtractionQualityStatus
from app.ai_interview.schemas.session import InterviewSessionSchema

def test_session_initializer_populates_context():
    blueprint = InterviewBlueprint(
        blueprint_version="1.0",
        total_question_budget=10,
        min_questions=5,
        max_questions=15,
        emergency_max_questions=20,
        topics=[
            # NOTE: .source values below are updated (as part of the D-03
            # prerequisite source->dimension bridge fix) from the old,
            # unrealistic literals ("requirement"/"resume"/"gap"/"behavioral"
            # -- core.enums.TopicSource values that TopicSelector/
            # CoveragePlanner never actually produce) to the REAL
            # TopicSourceCode strings the live pipeline generates. See
            # test_dimension_bridge.py for full, dedicated coverage of the
            # real TopicSelector -> CoveragePlanner -> SessionInitializer
            # pipeline; this test's purpose remains testing
            # SessionInitializer's broader context-population behavior
            # (criticality, resume_evidence, strategy/mixed_composition
            # propagation) in isolation.
            TopicBlueprint(
                topic_id="t1",
                topic_name="Python",
                source="ROLE_REQUIRED",
                priority=1,
                mandatory=True,
                initial_difficulty=DifficultyLevel.EASY,
                allowed_question_types=[QuestionType.INITIAL],
                question_budget=2
            ),
            TopicBlueprint(
                topic_id="t2",
                topic_name="React",
                source="PROJECT_EVIDENCE",
                priority=2,
                mandatory=True,
                initial_difficulty=DifficultyLevel.MEDIUM,
                allowed_question_types=[QuestionType.INITIAL],
                question_budget=2
            ),
            TopicBlueprint(
                topic_id="t3",
                topic_name="System Design",
                source="ROLE_REQUIRED",
                priority=3,
                mandatory=False,
                initial_difficulty=DifficultyLevel.HARD,
                allowed_question_types=[QuestionType.INITIAL],
                question_budget=2
            ),
            TopicBlueprint(
                topic_id="t4",
                topic_name="Leadership",
                source="MODE_REQUIRED",
                priority=4,
                mandatory=False,
                initial_difficulty=DifficultyLevel.EASY,
                allowed_question_types=[QuestionType.INITIAL],
                question_budget=2
            )
        ]
    )

    strategy_def = StrategyDefinition(
        strategy_id="test_strategy",
        name="Test",
        description="Test",
        min_questions=5,
        target_questions=10,
        max_questions=15,
        max_questions_per_topic=3,
        max_followups_per_topic=2,
        strong_threshold=0.8,
        acceptable_threshold=0.6,
        weak_threshold=0.4
    )

    mixed_comp = MixedComposition(
        technical=0.5,
        resume_experience=0.2,
        hr_behavioral=0.2,
        situational_case=0.1
    )

    campaign_reqs = [
        {"skill": "python", "criticality": "critical"},
        {"skill": "kubernetes", "criticality": "preferred"}
    ]

    resume = StructuredResume(
        skills=[Skill(name="React"), Skill(name="Python")]
    )
    
    candidate_context = CandidateInterviewContext(
        candidate_id="cand1",
        structured_resume=resume,
        extraction_metadata={
            "source_type": "pdf",
            "extractor_name": "test",
            "extractor_version": "1.0",
            "character_count": 100,
            "detected_sections": [],
            "warning_count": 0,
            "processing_duration_ms": 1.0
        },
        quality_status=ExtractionQualityStatus.USABLE,
        warnings=[]
    )

    session = SessionInitializer.initialize(
        blueprint=blueprint,
        candidate_id="cand1",
        company_id="comp1",
        campaign_id="camp1",
        mode_id="official",
        mode_version=1,
        strategy_snapshot=strategy_def,
        interview_type=InterviewType.MIXED,
        mixed_composition=mixed_comp,
        campaign_requirements=campaign_reqs,
        candidate_context=candidate_context
    )

    assert session.strategy_snapshot is not None
    assert session.strategy_snapshot.strategy_id == "test_strategy"
    assert session.interview_type == InterviewType.MIXED
    assert session.mixed_composition is not None
    assert session.mixed_composition.technical == 0.5

    topics = {t.topic_id: t for t in session.topic_progress}
    
    # NOTE: TopicProgress.source assertions below reflect the D-03
    # prerequisite #2 fix (TopicSourceCode -> TopicProgress.source bridge).
    # ROLE_REQUIRED resolves to REQUIREMENT when resume_evidence is present
    # (t1) and to GAP when resume_evidence is ABSENT (t3) -- see
    # _resolve_topic_source_from_source_codes in session_initializer.py for
    # the full mapping justification. See test_source_bridge.py for
    # dedicated coverage of the real TopicSelector -> CoveragePlanner ->
    # SessionInitializer pipeline.

    t1 = topics["t1"]
    assert t1.criticality == RequirementCriticality.CRITICAL
    assert t1.resume_evidence == ResumeEvidence.STRONG
    assert t1.dimension == TopicDimension.TECHNICAL  # ROLE_REQUIRED -> TECHNICAL
    assert t1.source == TopicSource.REQUIREMENT  # ROLE_REQUIRED + present on resume

    t2 = topics["t2"]
    assert t2.criticality is None
    assert t2.resume_evidence == ResumeEvidence.STRONG
    assert t2.dimension == TopicDimension.RESUME  # PROJECT_EVIDENCE -> RESUME
    assert t2.source == TopicSource.RESUME  # PROJECT_EVIDENCE -> RESUME

    t3 = topics["t3"]
    assert t3.criticality is None
    assert t3.resume_evidence == ResumeEvidence.ABSENT
    assert t3.dimension == TopicDimension.TECHNICAL  # ROLE_REQUIRED -> TECHNICAL
    assert t3.source == TopicSource.GAP  # ROLE_REQUIRED + absent from resume

    t4 = topics["t4"]
    assert t4.criticality is None
    assert t4.resume_evidence == ResumeEvidence.ABSENT
    assert t4.dimension == TopicDimension.BEHAVIORAL  # MODE_REQUIRED -> BEHAVIORAL
    assert t4.source == TopicSource.BEHAVIORAL  # MODE_REQUIRED -> BEHAVIORAL
