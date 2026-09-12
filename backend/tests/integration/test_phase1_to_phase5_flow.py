"""
End-to-End Architecture Flow Test (Phase 1 -> Phase 5)

This integration test verifies the deterministic architecture across all phases:
1. Core Domain schemas (Phase 1)
2. Resume Context structure (Phase 2)
3. Blueprint Generation (Phase 3)
4. Runtime Decision Control (Phase 4)
5. Question Generation & Mutation Safety (Phase 5)

This file is part of the final Phase 1-5 Integration Audit.
"""
import pytest
from datetime import datetime

from app.ai_interview.schemas.resume import StructuredResume, Skill, Project
from app.ai_interview.resume_processing.schemas import CandidateInterviewContext, ExtractionMetadata
from app.ai_interview.resume_processing.enums import ExtractionQualityStatus
from app.ai_interview.core.enums import InterviewModeStatus, InterviewState, TopicState
from app.ai_interview.schemas.interview_mode import InterviewModeDefinition, InterviewModeSettings

from app.ai_interview.blueprint_planning import InterviewBlueprintPlanner, BlueprintPlanningRequest, JobRequirementContext
from app.ai_interview.runtime import SessionInitializer, RuntimeController, RuntimeAction
from app.ai_interview.question_engine.question_engine import QuestionEngine
from app.ai_interview.question_engine.question_generator import FakeQuestionGenerator

@pytest.fixture
def e2e_context():
    """Mocked Phase 2 output: CandidateInterviewContext"""
    return CandidateInterviewContext(
        candidate_id="c_e2e_123",
        structured_resume=StructuredResume(
            skills=[Skill(name="Python")],
            projects=[Project(name="Backend Service", description="API", technologies=["Python"])]
        ),
        extraction_metadata=ExtractionMetadata(
            source_type="pdf",
            extractor_name="test",
            extractor_version="1.0",
            character_count=500,
            detected_sections=["skills", "projects"],
            warning_count=0,
            processing_duration_ms=10.0
        ),
        quality_status=ExtractionQualityStatus.USABLE,
        warnings=[]
    )

@pytest.fixture
def e2e_mode():
    """Phase 1 Configuration"""
    return InterviewModeDefinition(
        mode_id="mode_e2e",
        name="Backend Engineer Standard",
        description="Standard E2E mode",
        version=1,
        status=InterviewModeStatus.PUBLISHED,
        settings=InterviewModeSettings(
            allowed_question_types=["initial", "follow_up"],
            difficulty_policy="medium"
        ),
        created_at=datetime.utcnow()
    )

@pytest.fixture
def e2e_job_context():
    return JobRequirementContext(
        role_title="Backend Engineer",
        required_skills=["Python", "System Design"],
        interview_duration_minutes=30
    )


def test_full_phase1_to_phase5_happy_flow(e2e_context, e2e_mode, e2e_job_context):
    """
    Simulates the entire valid pipeline from CandidateContext to QuestionRecord.
    """
    # ── Phase 3: Blueprint Planning ──────────────────────────────────────────
    planner = InterviewBlueprintPlanner()
    request = BlueprintPlanningRequest(
        candidate_context=e2e_context,
        mode_definition=e2e_mode,
        job_context=e2e_job_context
    )
    blueprint = planner.plan(request)
    
    # Assert Blueprint created successfully
    assert len(blueprint.topics) >= 1
    assert blueprint.total_question_budget > 0
    
    # ── Phase 4: Session Initialization & Runtime ────────────────────────────
    session = SessionInitializer.initialize(
        blueprint=blueprint,
        candidate_id=e2e_context.candidate_id,
        company_id="company_test",
        campaign_id="campaign_test",
        mode_id=e2e_mode.mode_id,
        mode_version=e2e_mode.version
    )
    
    # Move through state machine to IN_PROGRESS and select a topic
    RuntimeController.execute_transition(session, RuntimeAction.INITIALIZE)
    RuntimeController.execute_transition(session, RuntimeAction.START)
    RuntimeController.execute_transition(session, RuntimeAction.ADVANCE_TOPIC)
    
    assert session.state == InterviewState.IN_PROGRESS
    assert session.current_topic_id is not None
    active_topic = next((t for t in session.topic_progress if t.topic_id == session.current_topic_id), None)
    assert active_topic is not None
    
    from app.ai_interview.runtime.topic_state_manager import TopicStateManager
    TopicStateManager.mark_in_progress(active_topic)
    
    assert active_topic.state == TopicState.IN_PROGRESS
    
    decision = RuntimeController.get_allowed_action(session)
    assert decision.active_topic_id == session.current_topic_id
    
    # ── Phase 5: Question Generation ─────────────────────────────────────────
    engine = QuestionEngine(generator=FakeQuestionGenerator(mode="valid"))
    
    # Pre-generation snapshot for mutation safety assertions
    pre_total_qs = session.questions_asked_total
    pre_topic_qs = active_topic.questions_asked
    
    result = engine.request_next_question(
        session=session,
        runtime_decision=decision,
        candidate_context=e2e_context,
        mode=e2e_mode
    )
    
    # ── End-to-End Verifications ─────────────────────────────────────────────
    assert result.success is True
    assert result.question_record is not None
    assert result.question_record.topic_id == session.current_topic_id
    
    # Verified: Exact single increment
    assert session.questions_asked_total == pre_total_qs + 1
    assert active_topic.questions_asked == pre_topic_qs + 1
    assert len(session.question_history) == 1
    
    # Verified: Runtime state ownership maintained
    assert session.state == InterviewState.IN_PROGRESS
    assert active_topic.state == TopicState.IN_PROGRESS


def test_full_phase1_to_phase5_generator_failure_flow(e2e_context, e2e_mode, e2e_job_context):
    """
    Simulates a failure in the non-deterministic generator to prove Session immutability.
    """
    # Setup Phase 3 & Phase 4
    planner = InterviewBlueprintPlanner()
    request = BlueprintPlanningRequest(
        candidate_context=e2e_context, mode_definition=e2e_mode, job_context=e2e_job_context
    )
    blueprint = planner.plan(request)
    session = SessionInitializer.initialize(
        blueprint=blueprint, candidate_id=e2e_context.candidate_id,
        company_id="company_test", campaign_id="campaign_test",
        mode_id=e2e_mode.mode_id, mode_version=e2e_mode.version
    )
    
    RuntimeController.execute_transition(session, RuntimeAction.INITIALIZE)
    RuntimeController.execute_transition(session, RuntimeAction.START)
    RuntimeController.execute_transition(session, RuntimeAction.ADVANCE_TOPIC)
    decision = RuntimeController.get_allowed_action(session)
    
    # Deep snapshot before failing generation
    pre_total_qs = session.questions_asked_total
    pre_history_len = len(session.question_history)
    active_topic = next((t for t in session.topic_progress if t.topic_id == session.current_topic_id), None)
    
    from app.ai_interview.runtime.topic_state_manager import TopicStateManager
    TopicStateManager.mark_in_progress(active_topic)
    
    pre_topic_qs = active_topic.questions_asked
    pre_state = session.state
    pre_topic_state = active_topic.state
    
    # Phase 5: Fake Generator raises an exception
    engine = QuestionEngine(generator=FakeQuestionGenerator(mode="raise"))
    result = engine.request_next_question(
        session=session, runtime_decision=decision, candidate_context=e2e_context, mode=e2e_mode
    )
    
    # Verifications
    assert result.success is False
    assert result.question_record is None
    
    # Most critical assertions: No state corruption
    assert session.questions_asked_total == pre_total_qs
    assert active_topic.questions_asked == pre_topic_qs
    assert len(session.question_history) == pre_history_len
    assert session.state == pre_state
    assert active_topic.state == pre_topic_state
