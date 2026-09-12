import pytest
from pydantic import ValidationError
from datetime import datetime, UTC

from app.ai_interview.core.enums import InterviewState, TopicState, DifficultyLevel, QuestionType, InterviewModeStatus
from app.ai_interview.schemas.session import TopicProgress, InterviewSessionSchema
from app.ai_interview.schemas.validation import ValidationResult
from app.ai_interview.schemas.interview_mode import InterviewModeDefinition, InterviewModeSettings
from app.ai_interview.schemas.evaluation import AnswerEvaluation
from app.ai_interview.schemas.readiness import ReadinessResult
from app.ai_interview.schemas.blueprint import InterviewBlueprint, TopicBlueprint


def test_enum_validation():
    # Valid assignments should not raise errors
    assert InterviewState.CREATED == "created"
    assert TopicState.COVERED == "covered"
    assert DifficultyLevel.HARD == "hard"
    
    # Invalid enum assignment via Pydantic model
    class MockModel(InterviewSessionSchema):
        pass
    
    with pytest.raises(ValidationError):
        TopicProgress(topic_id="t1", state="invalid_state")


def test_topic_state_semantics():
    tp1 = TopicProgress(
        topic_id="t1",
        state=TopicState.COVERED,
        structurally_attempted=True,
        qualitatively_covered=True
    )
    assert tp1.state == TopicState.COVERED
    
    tp2 = TopicProgress(
        topic_id="t2",
        state=TopicState.FAILED_ABANDONED,
        structurally_attempted=True,
        qualitatively_covered=False
    )
    assert tp2.state == TopicState.FAILED_ABANDONED
    
    with pytest.raises(ValidationError) as exc_info:
        TopicProgress(
            topic_id="t3",
            state=TopicState.FAILED_ABANDONED,
            structurally_attempted=False,
            qualitatively_covered=False
        )
    assert "FAILED_ABANDONED state requires structurally_attempted=True" in str(exc_info.value)
    
    with pytest.raises(ValidationError) as exc_info:
        TopicProgress(
            topic_id="t4",
            state=TopicState.COVERED,
            structurally_attempted=True,
            qualitatively_covered=False
        )
    assert "COVERED state requires structurally_attempted=True and qualitatively_covered=True" in str(exc_info.value)


def test_validation_result_semantics():
    vr1 = ValidationResult(
        passed=True,
        hard_failures=[],
        soft_warnings=["difficulty_alignment_warning"]
    )
    assert vr1.passed is True
    
    with pytest.raises(ValidationError) as exc_info:
        ValidationResult(
            passed=True,
            hard_failures=["duplicate_question"],
            soft_warnings=[]
        )
    assert "Validation cannot pass if there are hard failures" in str(exc_info.value)


def test_mode_version_data():
    mode = InterviewModeDefinition(
        mode_id="SWE_BACKEND",
        name="Backend SWE Interview",
        description="Standard backend software engineering interview mode.",
        version=1,
        status=InterviewModeStatus.PUBLISHED,
        settings=InterviewModeSettings(),
        created_at=datetime.now(UTC),
        published_at=datetime.now(UTC)
    )
    assert mode.mode_id == "SWE_BACKEND"
    assert mode.version == 1
    assert mode.status == InterviewModeStatus.PUBLISHED


def test_session_defaults():
    blueprint = InterviewBlueprint(
        blueprint_version="1.0",
        total_question_budget=10,
        min_questions=5,
        max_questions=15,
        emergency_max_questions=20,
        topics=[
            TopicBlueprint(topic_id="python", topic_name="Python", source="resume", priority=1)
        ]
    )
    
    session = InterviewSessionSchema(
        session_id="sess_123",
        candidate_id="cand_123",
        company_id="comp_123",
        campaign_id="camp_123",
        mode_id="SWE_BACKEND",
        mode_version=1,
        blueprint=blueprint,
        created_at=datetime.now(UTC)
    )
    
    assert session.state == InterviewState.CREATED
    assert session.questions_asked_total == 0


def test_score_range_validation():
    eval1 = AnswerEvaluation(
        correctness_score=0.8,
        depth_score=0.7,
        clarity_score=0.9,
        confidence_score=0.85,
        evaluation_summary="Good answer."
    )
    assert eval1.correctness_score == 0.8
    
    with pytest.raises(ValidationError):
        AnswerEvaluation(
            correctness_score=-0.1,
            depth_score=0.7,
            clarity_score=0.9,
            confidence_score=0.85,
            evaluation_summary="Bad score."
        )
        
    with pytest.raises(ValidationError):
        ReadinessResult(
            score=1.2,
            confidence=0.9,
        )


from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_mongodb_index_uniqueness():
    from app.db.indexes import create_indexes
    with patch("app.db.indexes.get_database") as mock_get_db:
        mock_db = AsyncMock()
        mock_get_db.return_value = mock_db
        
        mock_db.interview_mode_definitions.create_index = AsyncMock()
        mock_db.interview_sessions.create_index = AsyncMock()
        mock_db.interview_turns.create_index = AsyncMock()
        mock_db.interview_reports.create_index = AsyncMock()

        await create_indexes()

        mock_db.interview_mode_definitions.create_index.assert_any_call(
            [("mode_id", 1), ("version", 1)],
            unique=True,
            name="idx_mode_version_unique"
        )
        
        mock_db.interview_sessions.create_index.assert_any_call(
            "session_id",
            unique=True,
            name="idx_session_id_unique"
        )
        
        mock_db.interview_turns.create_index.assert_any_call(
            [("session_id", 1), ("turn_number", 1)],
            unique=True,
            name="idx_turn_session_unique"
        )
        
        mock_db.interview_reports.create_index.assert_any_call(
            "session_id",
            unique=True,
            name="idx_report_session_unique"
        )

@pytest.mark.asyncio
async def test_mode_repository_immutability():
    from app.repositories.interview_mode_repository import InterviewModeRepository
    from bson import ObjectId
    
    with patch("app.repositories.base_repository.get_database") as mock_get_db:
        mock_db = AsyncMock()
        mock_get_db.return_value = mock_db
        mock_collection = AsyncMock()
        mock_db.__getitem__.return_value = mock_collection
        
        repo = InterviewModeRepository()
        
        # Test 1: Document doesn't exist
        mock_collection.update_one.return_value.matched_count = 0
        
        # Mock get_by_id to return None (not found)
        repo.get_by_id = AsyncMock(return_value=None)
        
        with pytest.raises(ValueError) as exc_info:
            await repo.update("64cbbdbb1f417534b8c9d123", {"status": InterviewModeStatus.DRAFT})
            
        assert "Document not found" in str(exc_info.value)

        # Test 2: Document is published
        repo.get_by_id = AsyncMock(return_value={"_id": ObjectId("64cbbdbb1f417534b8c9d123"), "status": InterviewModeStatus.PUBLISHED})
        
        with pytest.raises(ValueError) as exc_info:
            await repo.update("64cbbdbb1f417534b8c9d123", {"status": InterviewModeStatus.DRAFT})
        
        assert "Cannot modify a published interview mode" in str(exc_info.value)
        
        mock_collection.update_one.assert_called_with(
            {"_id": ObjectId("64cbbdbb1f417534b8c9d123"), "status": {"$ne": InterviewModeStatus.PUBLISHED}},
            {"$set": {"status": InterviewModeStatus.DRAFT}}
        )
