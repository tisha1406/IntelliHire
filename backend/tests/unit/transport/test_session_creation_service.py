import pytest
import uuid
from unittest.mock import AsyncMock, patch, MagicMock

from app.auth.jwt_handler import TokenPayload
from app.ai_interview.transport.services.session_creation_service import SessionCreationService
from app.ai_interview.core.enums import InterviewState
from app.ai_interview.question_engine.enums import QuestionStatus
from app.ai_interview.resume_processing.schemas import CandidateInterviewContext, StructuredResume, ExtractionMetadata
from app.ai_interview.resume_processing.enums import ExtractionQualityStatus
from app.ai_interview.schemas.session import InterviewSessionSchema, OperationClaim
from app.ai_interview.question_engine.schemas import QuestionRecord
from app.ai_interview.schemas.blueprint import InterviewBlueprint
from datetime import datetime, timezone, timedelta

@pytest.fixture
def mock_repos():
    return {
        "campaign_repo": AsyncMock(),
        "mode_repo": AsyncMock(),
        "resume_repo": AsyncMock(),
        "candidate_repo": AsyncMock(),
        "session_repo": AsyncMock()
    }

@pytest.fixture
def service(mock_repos):
    return SessionCreationService(**mock_repos)

@pytest.fixture
def token():
    return TokenPayload(sub="u1", user_id="u1", role="candidate", company_id="comp1", candidate_id="cand1", exp=9999999999, iat=1)

@pytest.mark.asyncio
async def test_normal_active_in_progress_session(service, token, mock_repos):
    campaign_id = "camp1"
    
    mock_repos["campaign_repo"].get_by_id.return_value = {"status": "active", "company_id": "comp1", "interview_mode": "m1"}
    mock_repos["candidate_repo"].get.return_value = {"campaign_id": "camp1"}
    
    blueprint = InterviewBlueprint(mode_id="m1", blueprint_version="1", min_questions=1, max_questions=5, total_question_budget=5, emergency_max_questions=10, topics=[])
    
    # Existing session with a DISPATCHED question
    existing_session = InterviewSessionSchema(
        session_id="s1",
        candidate_id="cand1",
        company_id="comp1",
        campaign_id="camp1",
        mode_id="m1",
        mode_version=1,
        created_at=datetime.now(timezone.utc),
        state=InterviewState.IN_PROGRESS,
        version=1,
        question_history=[
            QuestionRecord(session_id="s1", turn_number=1, record_id="q1", topic_id="t1", question_text="q", status=QuestionStatus.DISPATCHED, question_type="initial", difficulty="medium")
        ],
        blueprint=blueprint
    )
    mock_repos["session_repo"].find_active_session.return_value = existing_session
    
    result = await service.create_session(token, campaign_id)
    
    assert result["session_id"] == "s1"
    assert result["state"] == InterviewState.IN_PROGRESS.value
    mock_repos["session_repo"].save.assert_not_called()


@pytest.mark.asyncio
async def test_stuck_in_progress_session_fails_and_creates_new(service, token, mock_repos):
    campaign_id = "camp1"
    
    mock_repos["campaign_repo"].get_by_id.return_value = {"status": "active", "company_id": "comp1", "interview_mode": "m1"}
    mock_repos["candidate_repo"].get.return_value = {"campaign_id": "camp1"}
    mock_repos["mode_repo"].get_by_mode_id.return_value = {"mode_id": "m1", "version": 1, "name": "mode", "description": "desc", "status": "published", "created_at": "2024-01-01T00:00:00Z", "settings": {}}
    mock_repos["resume_repo"].get_by_candidate.return_value = {"id": "r1"}
    
    blueprint = InterviewBlueprint(mode_id="m1", blueprint_version="1", min_questions=1, max_questions=5, total_question_budget=5, emergency_max_questions=10, topics=[])
    
    # Stuck session: IN_PROGRESS but last question is EVALUATED
    stuck_session = InterviewSessionSchema(
        session_id="stuck1",
        candidate_id="cand1",
        company_id="comp1",
        campaign_id="camp1",
        mode_id="m1",
        mode_version=1,
        created_at=datetime.now(timezone.utc),
        state=InterviewState.IN_PROGRESS,
        version=1,
        generation_claim=OperationClaim(
            claim_id="claim1",
            claimed_at=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=1)
        ),
        question_history=[
            QuestionRecord(
                session_id="stuck1",
                turn_number=1,
                record_id="q1",
                topic_id="t1",
                question_text="q",
                status=QuestionStatus.EVALUATED,
                question_type="initial",
                difficulty="medium",
                evaluation_claim=OperationClaim(
                    claim_id="eval_claim1",
                    claimed_at=datetime.now(timezone.utc),
                    expires_at=datetime.now(timezone.utc) + timedelta(minutes=1)
                )
            )
        ],
        blueprint=blueprint
    )
    mock_repos["session_repo"].find_active_session.return_value = stuck_session
    
    # Mock resolve_interview_mode to just return m1
    with patch("app.ai_interview.transport.services.session_creation_service.resolve_interview_mode", return_value="m1"), \
         patch("app.ai_interview.transport.services.session_creation_service.ResumeContextBridge.build") as mock_bridge, \
         patch("app.ai_interview.transport.services.session_creation_service.JobRequirementContext"), \
         patch("app.ai_interview.transport.services.session_creation_service.BlueprintPlanningRequest"), \
         patch("app.ai_interview.transport.services.session_creation_service.SessionInitializer.initialize") as mock_init, \
         patch.object(service.planner, "plan", return_value=blueprint):
        
        mock_init.return_value = InterviewSessionSchema(
            session_id="new1",
            candidate_id="cand1",
            company_id="comp1",
            campaign_id="camp1",
            mode_id="m1",
            mode_version=1,
            created_at=datetime.now(timezone.utc),
            state=InterviewState.CREATED,
            version=0,
            question_history=[],
            blueprint=blueprint
        )
        
        result = await service.create_session(token, campaign_id)
        
        # Verify the stuck session was failed, claim released, and saved
        assert stuck_session.state == InterviewState.FAILED
        assert stuck_session.generation_claim is None
        assert stuck_session.question_history[0].evaluation_claim is None
        mock_repos["session_repo"].save.assert_any_call(stuck_session, expected_version=1)
        
        # Verify a new session was created and returned
        assert result["session_id"] == "new1"
        assert result["state"] == InterviewState.CREATED.value
        mock_repos["session_repo"].save.assert_any_call(mock_init.return_value, expected_version=0)


@pytest.mark.asyncio
async def test_stuck_in_progress_session_without_claim_fails_and_creates_new(service, token, mock_repos):
    campaign_id = "camp1"

    mock_repos["campaign_repo"].get_by_id.return_value = {"status": "active", "company_id": "comp1", "interview_mode": "m1"}
    mock_repos["candidate_repo"].get.return_value = {"campaign_id": "camp1"}
    mock_repos["mode_repo"].get_by_mode_id.return_value = {"mode_id": "m1", "version": 1, "name": "mode", "description": "desc", "status": "published", "created_at": "2024-01-01T00:00:00Z", "settings": {}}
    mock_repos["resume_repo"].get_by_candidate.return_value = {"id": "r1"}

    blueprint = InterviewBlueprint(mode_id="m1", blueprint_version="1", min_questions=1, max_questions=5, total_question_budget=5, emergency_max_questions=10, topics=[])

    # Stuck session: IN_PROGRESS but last question is EVALUATED (no claim)
    stuck_session = InterviewSessionSchema(
        session_id="stuck2",
        candidate_id="cand1",
        company_id="comp1",
        campaign_id="camp1",
        mode_id="m1",
        mode_version=1,
        created_at=datetime.now(timezone.utc),
        state=InterviewState.IN_PROGRESS,
        version=1,
        generation_claim=None,
        question_history=[
            QuestionRecord(session_id="stuck2", turn_number=1, record_id="q1", topic_id="t1", question_text="q", status=QuestionStatus.EVALUATED, question_type="initial", difficulty="medium")
        ],
        blueprint=blueprint
    )

    mock_repos["session_repo"].find_active_session.return_value = stuck_session

    with patch("app.ai_interview.transport.services.session_creation_service.resolve_interview_mode", return_value="m1"), \
         patch("app.ai_interview.transport.services.session_creation_service.ResumeContextBridge.build"), \
         patch("app.ai_interview.transport.services.session_creation_service.JobRequirementContext"), \
         patch("app.ai_interview.transport.services.session_creation_service.BlueprintPlanningRequest"), \
         patch("app.ai_interview.transport.services.session_creation_service.SessionInitializer.initialize") as mock_init, \
         patch.object(service.planner, "plan", return_value=blueprint):
        
        mock_init.return_value = InterviewSessionSchema(
            session_id="new2",
            candidate_id="cand1",
            company_id="comp1",
            campaign_id="camp1",
            mode_id="m1",
            mode_version=1,
            created_at=datetime.now(timezone.utc),
            state=InterviewState.CREATED,
            version=0,
            question_history=[],
            blueprint=blueprint
        )
        
        result = await service.create_session(token, campaign_id)
        
        # Verify the stuck session was failed, claim released, and saved
        assert stuck_session.state == InterviewState.FAILED
        assert stuck_session.generation_claim is None
        assert stuck_session.question_history[0].evaluation_claim is None
        mock_repos["session_repo"].save.assert_any_call(stuck_session, expected_version=1)
        
        # Verify a new session was created and returned
        assert result["session_id"] == "new2"


@pytest.mark.asyncio
async def test_stuck_in_progress_session_only_evaluation_claim_fails_and_creates_new(service, token, mock_repos):
    campaign_id = "camp1"

    mock_repos["campaign_repo"].get_by_id.return_value = {"status": "active", "company_id": "comp1", "interview_mode": "m1"}
    mock_repos["candidate_repo"].get.return_value = {"campaign_id": "camp1"}
    mock_repos["mode_repo"].get_by_mode_id.return_value = {"mode_id": "m1", "version": 1, "name": "mode", "description": "desc", "status": "published", "created_at": "2024-01-01T00:00:00Z", "settings": {}}
    mock_repos["resume_repo"].get_by_candidate.return_value = {"id": "r1"}

    blueprint = InterviewBlueprint(mode_id="m1", blueprint_version="1", min_questions=1, max_questions=5, total_question_budget=5, emergency_max_questions=10, topics=[])

    stuck_session = InterviewSessionSchema(
        session_id="stuck3",
        candidate_id="cand1",
        company_id="comp1",
        campaign_id="camp1",
        mode_id="m1",
        mode_version=1,
        created_at=datetime.now(timezone.utc),
        state=InterviewState.IN_PROGRESS,
        version=1,
        generation_claim=None,
        question_history=[
            QuestionRecord(
                session_id="stuck3",
                turn_number=1,
                record_id="q1",
                topic_id="t1",
                question_text="q",
                status=QuestionStatus.EVALUATED,
                question_type="initial",
                difficulty="medium",
                evaluation_claim=OperationClaim(
                    claim_id="eval_claim2",
                    claimed_at=datetime.now(timezone.utc),
                    expires_at=datetime.now(timezone.utc) + timedelta(minutes=1)
                )
            )
        ],
        blueprint=blueprint
    )

    mock_repos["session_repo"].find_active_session.return_value = stuck_session

    with patch("app.ai_interview.transport.services.session_creation_service.resolve_interview_mode", return_value="m1"), \
         patch("app.ai_interview.transport.services.session_creation_service.ResumeContextBridge.build"), \
         patch("app.ai_interview.transport.services.session_creation_service.JobRequirementContext"), \
         patch("app.ai_interview.transport.services.session_creation_service.BlueprintPlanningRequest"), \
         patch("app.ai_interview.transport.services.session_creation_service.SessionInitializer.initialize") as mock_init, \
         patch.object(service.planner, "plan", return_value=blueprint):
        
        mock_init.return_value = InterviewSessionSchema(
            session_id="new3",
            candidate_id="cand1",
            company_id="comp1",
            campaign_id="camp1",
            mode_id="m1",
            mode_version=1,
            created_at=datetime.now(timezone.utc),
            state=InterviewState.CREATED,
            version=0,
            question_history=[],
            blueprint=blueprint
        )
        
        result = await service.create_session(token, campaign_id)
        
        assert stuck_session.state == InterviewState.FAILED
        assert stuck_session.generation_claim is None
        assert stuck_session.question_history[0].evaluation_claim is None
        mock_repos["session_repo"].save.assert_any_call(stuck_session, expected_version=1)
        assert result["session_id"] == "new3"

@pytest.mark.asyncio
async def test_existing_failed_session(service, token, mock_repos):
    campaign_id = "camp1"
    
    mock_repos["campaign_repo"].get_by_id.return_value = {"status": "active", "company_id": "comp1", "interview_mode": "m1"}
    mock_repos["candidate_repo"].get.return_value = {"campaign_id": "camp1"}
    mock_repos["mode_repo"].get_by_mode_id.return_value = {"mode_id": "m1", "version": 1, "name": "mode", "description": "desc", "status": "published", "created_at": "2024-01-01T00:00:00Z", "settings": {}}
    mock_repos["resume_repo"].get_by_candidate.return_value = {"id": "r1"}
    
    mock_repos["session_repo"].find_active_session.return_value = None
    
    blueprint = InterviewBlueprint(mode_id="m1", blueprint_version="1", min_questions=1, max_questions=5, total_question_budget=5, emergency_max_questions=10, topics=[])
    
    with patch("app.ai_interview.transport.services.session_creation_service.resolve_interview_mode", return_value="m1"), \
         patch("app.ai_interview.transport.services.session_creation_service.ResumeContextBridge.build"), \
         patch("app.ai_interview.transport.services.session_creation_service.JobRequirementContext"), \
         patch("app.ai_interview.transport.services.session_creation_service.BlueprintPlanningRequest"), \
         patch("app.ai_interview.transport.services.session_creation_service.SessionInitializer.initialize") as mock_init, \
         patch.object(service.planner, "plan", return_value=blueprint):
        
        mock_init.return_value = InterviewSessionSchema(
            session_id="new1",
            candidate_id="cand1",
            company_id="comp1",
            campaign_id="camp1",
            mode_id="m1",
            mode_version=1,
            created_at=datetime.now(timezone.utc),
            state=InterviewState.CREATED,
            version=0,
            question_history=[],
            blueprint=blueprint
        )
        
        result = await service.create_session(token, campaign_id)
        assert result["session_id"] == "new1"
        assert result["state"] == InterviewState.CREATED.value


@pytest.mark.asyncio
async def test_existing_completed_session(service, token, mock_repos):
    campaign_id = "camp1"
    
    mock_repos["campaign_repo"].get_by_id.return_value = {"status": "active", "company_id": "comp1", "interview_mode": "m1"}
    mock_repos["candidate_repo"].get.return_value = {"campaign_id": "camp1"}
    mock_repos["mode_repo"].get_by_mode_id.return_value = {"mode_id": "m1", "version": 1, "name": "mode", "description": "desc", "status": "published", "created_at": "2024-01-01T00:00:00Z", "settings": {}}
    mock_repos["resume_repo"].get_by_candidate.return_value = {"id": "r1"}
    
    mock_repos["session_repo"].find_active_session.return_value = None
    
    blueprint = InterviewBlueprint(mode_id="m1", blueprint_version="1", min_questions=1, max_questions=5, total_question_budget=5, emergency_max_questions=10, topics=[])
    
    with patch("app.ai_interview.transport.services.session_creation_service.resolve_interview_mode", return_value="m1"), \
         patch("app.ai_interview.transport.services.session_creation_service.ResumeContextBridge.build"), \
         patch("app.ai_interview.transport.services.session_creation_service.JobRequirementContext"), \
         patch("app.ai_interview.transport.services.session_creation_service.BlueprintPlanningRequest"), \
         patch("app.ai_interview.transport.services.session_creation_service.SessionInitializer.initialize") as mock_init, \
         patch.object(service.planner, "plan", return_value=blueprint):
        
        mock_init.return_value = InterviewSessionSchema(
            session_id="new1",
            candidate_id="cand1",
            company_id="comp1",
            campaign_id="camp1",
            mode_id="m1",
            mode_version=1,
            created_at=datetime.now(timezone.utc),
            state=InterviewState.CREATED,
            version=0,
            question_history=[],
            blueprint=blueprint
        )
        
        result = await service.create_session(token, campaign_id)
        assert result["session_id"] == "new1"
        assert result["state"] == InterviewState.CREATED.value

@pytest.mark.asyncio
async def test_create_session_is_practice(service, token, mock_repos):
    campaign_id = "camp1"
    
    mock_repos["campaign_repo"].get_by_id.return_value = {"status": "active", "company_id": "comp1", "interview_mode": "m1"}
    mock_repos["candidate_repo"].get.return_value = {"campaign_id": "camp1"}
    mock_repos["resume_repo"].get_by_candidate.return_value = {"id": "r1"}
    
    mock_repos["session_repo"].find_active_session.return_value = None
    
    # Do not mock resolve_interview_mode, JobRequirementContext, BlueprintPlanningRequest, 
    # because we want to see them bypassed or used correctly internally.
    # We DO mock SessionInitializer.initialize and ResumeContextBridge.build.
    
    with patch("app.ai_interview.transport.services.session_creation_service.ResumeContextBridge.build") as mock_bridge, \
         patch("app.ai_interview.transport.services.session_creation_service.SessionInitializer.initialize") as mock_init:
        
        mock_bridge.return_value = CandidateInterviewContext(
            candidate_id="cand1",
            structured_resume=StructuredResume(
                skills=[],
                experience=[],
                projects=[],
                education=[]
            ),
            extraction_metadata=ExtractionMetadata(
                source_type="pdf",
                extractor_name="mock",
                extractor_version="1",
                character_count=100,
                detected_sections=[],
                warning_count=0,
                processing_duration_ms=1.0
            ),
            quality_status=ExtractionQualityStatus.USABLE,
            warnings=[]
        )
        
        # We need a real planner response for assertions
        def fake_initialize(*args, **kwargs):
            return InterviewSessionSchema(
                session_id="pract1",
                candidate_id="cand1",
                company_id="comp1",
                campaign_id="camp1",
                mode_id=kwargs["mode_id"],
                mode_version=kwargs["mode_version"],
                created_at=datetime.now(timezone.utc),
                state=InterviewState.CREATED,
                version=0,
                question_history=[],
                blueprint=kwargs["blueprint"]
            )
        
        mock_init.side_effect = fake_initialize
        
        result = await service.create_session(token, campaign_id, is_practice=True)
        
        assert result["session_id"] == "pract1"
        assert result["mode_id"] == "practice"
        assert result["total_question_budget"] == 3
        assert result["topics_count"] == 3
        
        # Verify initializer was called with the right blueprint
        init_call_kwargs = mock_init.call_args.kwargs
        blueprint = init_call_kwargs["blueprint"]
        
        assert blueprint.total_question_budget == 3
        assert len(blueprint.topics) == 3
        topic_names = [t.topic_name for t in blueprint.topics]
        assert "Welcome to IntelliHire Practice. Could you tell me a little bit about yourself?" in topic_names
        assert "What made you interested in practicing your interview skills today?" in topic_names
        assert "What is one professional skill you are hoping to improve this year?" in topic_names

@pytest.mark.asyncio
async def test_session_creation_snapshots_campaign_voice(service, token, mock_repos):
    campaign_id = "camp1"
    mock_repos["campaign_repo"].get_by_id.return_value = {"status": "active", "company_id": "comp1", "interview_mode": "m1", "voice_id": "simran"}
    mock_repos["candidate_repo"].get.return_value = {"campaign_id": "camp1"}
    mock_repos["mode_repo"].get_by_mode_id.return_value = {"mode_id": "m1", "version": 1, "name": "mode", "description": "desc", "status": "published", "created_at": "2024-01-01T00:00:00Z", "settings": {}}
    mock_repos["resume_repo"].get_by_candidate.return_value = {"id": "r1"}
    mock_repos["session_repo"].find_active_session.return_value = None
    
    with patch("app.ai_interview.transport.services.session_creation_service.InterviewBlueprintPlanner.plan") as mock_plan:
        from app.ai_interview.schemas.blueprint import InterviewBlueprint, TopicBlueprint
        dummy_topic = TopicBlueprint(topic_id="t1", topic_name="name", source="req", priority=1, initial_difficulty="medium", allowed_question_types=[])
        mock_plan.return_value = InterviewBlueprint(mode_id="m1", blueprint_version="1", min_questions=1, max_questions=5, total_question_budget=5, emergency_max_questions=10, topics=[dummy_topic])
        
        result = await service.create_session(token, campaign_id)
        
        saved_session = mock_repos["session_repo"].save.call_args[0][0]
        assert saved_session.voice_id == "simran"

@pytest.mark.asyncio
async def test_session_creation_snapshots_campaign_voice_practice(service, token, mock_repos):
    campaign_id = "camp1"
    mock_repos["campaign_repo"].get_by_id.return_value = {"status": "active", "company_id": "comp1", "interview_mode": "m1", "voice_id": "sunny"}
    mock_repos["candidate_repo"].get.return_value = {"campaign_id": "camp1"}
    mock_repos["session_repo"].find_active_session.return_value = None
    
    with patch("app.ai_interview.transport.services.session_creation_service.SessionInitializer.initialize") as mock_init, \
         patch("app.ai_interview.transport.services.session_creation_service.ResumeContextBridge.build") as mock_bridge:
        def fake_initialize(*args, **kwargs):
            return InterviewSessionSchema(
                session_id="pract1",
                candidate_id="cand1",
                company_id="comp1",
                campaign_id="camp1",
                mode_id=kwargs["mode_id"],
                mode_version=kwargs["mode_version"],
                created_at=datetime.now(timezone.utc),
                state=InterviewState.CREATED,
                version=0,
                question_history=[],
                blueprint=kwargs["blueprint"],
                voice_id=kwargs.get("voice_id")
            )
        mock_init.side_effect = fake_initialize
        mock_bridge.return_value = None
        result = await service.create_session(token, campaign_id, is_practice=True)

        saved_session = mock_repos["session_repo"].save.call_args[0][0]
        assert saved_session.voice_id == "sunny"


# ─────────────────────────────────────────────────────────────────────────────
# Task 15 — Breadth Screening dynamic question budget (budget_mode="distinct_topics")
#
# The strategies collection stores Breadth Screening's min/target/max_questions
# as 0/0/0 -- a placeholder meaning "resolve from the final distinct topic
# count", not a literal budget. CompletionEngine (untouched by this fix) reads
# session.strategy_snapshot.{min,target,max}_questions literally, so without
# resolution a Breadth Screening session would complete immediately with zero
# questions (asked=0 >= max_questions=0). These tests drive the real
# SessionCreationService.create_session() (SessionInitializer.initialize is
# NOT mocked, matching test_session_creation_snapshots_campaign_voice above)
# and inspect the actual session persisted via session_repo.save().
# ─────────────────────────────────────────────────────────────────────────────

def _breadth_screening_definition():
    """Mirrors the real breadth_screening document (backend/seed_strategies.py)."""
    return {
        "strategy_id": "breadth_screening",
        "name": "Breadth Screening",
        "description": "Fast first-pass screening that checks breadth across distinct topics with minimal follow-up.",
        "version": 1,
        "is_active": True,
        "applicable_interview_types": ["technical", "resume_experience", "hr_behavioral", "situational_case", "mixed"],
        "budget_mode": "distinct_topics",
        "min_questions": 0,
        "target_questions": 0,
        "max_questions": 0,
        "max_questions_per_topic": 1,
        "max_followups_per_topic": 1,
        "strong_threshold": 0.8,
        "acceptable_threshold": 0.6,
        "weak_threshold": 0.4,
        "topic_selection_policy": {"policy_type": "round_robin"},
        "difficulty_policy": {
            "adapts": False, "scope": "global", "reset_on_switch": False,
            "step_size": 0, "band_constrainable": False,
        },
        "followup_policy": {"allowed_categories": ["followup_clarification"], "max_per_topic": 1},
        "gap_policy": {"enabled": False, "max_share_of_budget": 0.0},
        "completion_policy": {"allow_early_exit": True, "require_all_critical_covered": False},
        "company_override_bounds": {
            "target_questions_min_delta": -5, "target_questions_max_delta": 5,
            "allowed_difficulty_bands": ["medium"],
        },
    }


def _fixed_coverage_definition():
    """Mirrors the real fixed_coverage document -- budget_mode="fixed", must never be resolved."""
    return {
        "strategy_id": "fixed_coverage",
        "name": "Fixed Coverage",
        "description": "Consistent interview structure where candidates receive the same overall interview shape and topic coverage.",
        "version": 1,
        "is_active": True,
        "applicable_interview_types": ["technical", "resume_experience", "hr_behavioral", "situational_case", "mixed"],
        "budget_mode": "fixed",
        "min_questions": 10,
        "target_questions": 10,
        "max_questions": 10,
        "max_questions_per_topic": 2,
        "max_followups_per_topic": 1,
        "strong_threshold": 0.8,
        "acceptable_threshold": 0.6,
        "weak_threshold": 0.4,
        "completion_policy": {"allow_early_exit": True, "require_all_critical_covered": True},
        "company_override_bounds": {
            "target_questions_min_delta": -5, "target_questions_max_delta": 5,
            "allowed_difficulty_bands": ["easy", "medium", "hard"],
        },
    }


def _adaptive_depth_definition():
    """A second budget_mode="fixed" strategy, to prove the fix is specific to distinct_topics."""
    return {
        "strategy_id": "adaptive_depth",
        "name": "Adaptive Depth",
        "description": "Adapts follow-up depth based on candidate performance.",
        "version": 1,
        "is_active": True,
        "applicable_interview_types": ["technical", "mixed"],
        "budget_mode": "fixed",
        "min_questions": 8,
        "target_questions": 10,
        "max_questions": 12,
        "max_questions_per_topic": 3,
        "max_followups_per_topic": 2,
        "strong_threshold": 0.8,
        "acceptable_threshold": 0.6,
        "weak_threshold": 0.4,
        "completion_policy": {"allow_early_exit": True, "require_all_critical_covered": True},
    }


def _make_blueprint_plan_mock(num_topics):
    from app.ai_interview.schemas.blueprint import InterviewBlueprint, TopicBlueprint
    topics = [
        TopicBlueprint(
            topic_id=f"t{i+1}", topic_name=f"Topic {i+1}", source="req",
            priority=1, initial_difficulty="medium", allowed_question_types=[],
        )
        for i in range(num_topics)
    ]
    return InterviewBlueprint(
        mode_id="m1", blueprint_version="1", min_questions=1, max_questions=5,
        total_question_budget=5, emergency_max_questions=10, topics=topics,
    )


async def _create_session_with_strategy(service, token, mock_repos, campaign_id, definition, num_topics):
    mock_repos["campaign_repo"].get_by_id.return_value = {
        "status": "active", "company_id": "comp1", "interview_mode": "m1",
        "strategy_snapshot": {"definition": definition},
    }
    mock_repos["candidate_repo"].get.return_value = {"campaign_id": campaign_id}
    mock_repos["mode_repo"].get_by_mode_id.return_value = {
        "mode_id": "m1", "version": 1, "name": "mode", "description": "desc",
        "status": "published", "created_at": "2024-01-01T00:00:00Z", "settings": {},
    }
    mock_repos["resume_repo"].get_by_candidate.return_value = {"id": "r1"}
    mock_repos["session_repo"].find_active_session.return_value = None

    with patch(
        "app.ai_interview.transport.services.session_creation_service.InterviewBlueprintPlanner.plan"
    ) as mock_plan:
        mock_plan.return_value = _make_blueprint_plan_mock(num_topics)
        await service.create_session(token, campaign_id)

    return mock_repos["session_repo"].save.call_args[0][0]


@pytest.mark.asyncio
@pytest.mark.parametrize("num_topics", [3, 5, 10])
async def test_breadth_screening_resolves_budget_to_distinct_topic_count(service, token, mock_repos, num_topics):
    definition = _breadth_screening_definition()
    saved_session = await _create_session_with_strategy(
        service, token, mock_repos, "camp-breadth", definition, num_topics
    )

    snap = saved_session.strategy_snapshot
    assert snap.min_questions == num_topics
    assert snap.target_questions == num_topics
    assert snap.max_questions == num_topics


@pytest.mark.asyncio
async def test_breadth_screening_zero_topics_hits_the_existing_empty_blueprint_guard(service, token, mock_repos):
    """len(blueprint.topics) == 0 would naturally resolve min=target=max=0 (no
    invented fallback is introduced), but that state is never actually
    reachable: SessionInitializer.initialize() already rejects ANY blueprint
    with zero topics, for every strategy, before strategy_snapshot or
    CompletionEngine ever come into play (session_initializer.py: 'Cannot
    initialize session with empty blueprint.'). This is the existing guard
    the Task 15 audit was told to look for instead of inventing new
    zero-topic behavior -- confirmed here rather than assumed."""
    from app.ai_interview.runtime.exceptions import SessionInitializationError

    definition = _breadth_screening_definition()
    with pytest.raises(SessionInitializationError, match="empty blueprint"):
        await _create_session_with_strategy(
            service, token, mock_repos, "camp-breadth-zero", definition, num_topics=0
        )


@pytest.mark.asyncio
async def test_fixed_coverage_budget_is_not_resolved_from_topic_count(service, token, mock_repos):
    definition = _fixed_coverage_definition()
    saved_session = await _create_session_with_strategy(
        service, token, mock_repos, "camp-fixed", definition, num_topics=5
    )

    snap = saved_session.strategy_snapshot
    assert snap.min_questions == 10
    assert snap.target_questions == 10
    assert snap.max_questions == 10


@pytest.mark.asyncio
async def test_adaptive_depth_budget_is_not_resolved_from_topic_count(service, token, mock_repos):
    definition = _adaptive_depth_definition()
    saved_session = await _create_session_with_strategy(
        service, token, mock_repos, "camp-adaptive", definition, num_topics=7
    )

    snap = saved_session.strategy_snapshot
    assert snap.min_questions == 8
    assert snap.target_questions == 10
    assert snap.max_questions == 12


@pytest.mark.asyncio
async def test_breadth_screening_resolution_does_not_mutate_the_source_definition_dict(service, token, mock_repos):
    definition = _breadth_screening_definition()
    await _create_session_with_strategy(
        service, token, mock_repos, "camp-breadth-nomutate", definition, num_topics=4
    )

    # The dict passed in as campaign.strategy_snapshot["definition"] (standing
    # in for the campaign document / strategies collection) must be untouched.
    assert definition["min_questions"] == 0
    assert definition["target_questions"] == 0
    assert definition["max_questions"] == 0


@pytest.mark.asyncio
async def test_breadth_screening_resolved_snapshot_preserves_all_other_fields(service, token, mock_repos):
    definition = _breadth_screening_definition()
    saved_session = await _create_session_with_strategy(
        service, token, mock_repos, "camp-breadth-preserve", definition, num_topics=6
    )

    snap = saved_session.strategy_snapshot
    assert snap.strategy_id == "breadth_screening"
    assert snap.name == "Breadth Screening"
    assert snap.version == 1
    assert snap.budget_mode == "distinct_topics"
    assert set(t.value for t in snap.applicable_interview_types) == {
        "technical", "resume_experience", "hr_behavioral", "situational_case", "mixed",
    }
    assert snap.max_questions_per_topic == 1
    assert snap.max_followups_per_topic == 1
    assert snap.strong_threshold == 0.8
    assert snap.acceptable_threshold == 0.6
    assert snap.weak_threshold == 0.4
    assert snap.topic_selection_policy.policy_type == "round_robin"
    assert snap.difficulty_policy.adapts is False
    assert snap.completion_policy.allow_early_exit is True
    assert snap.completion_policy.require_all_critical_covered is False
    assert snap.company_override_bounds.target_questions_min_delta == -5

