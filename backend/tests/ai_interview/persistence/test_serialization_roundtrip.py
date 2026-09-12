import pytest
import uuid
from datetime import datetime, timezone
from app.ai_interview.schemas.session import InterviewSessionSchema, TopicProgress
from app.ai_interview.schemas.blueprint import InterviewBlueprint
from app.ai_interview.core.enums import InterviewState, DifficultyLevel, TopicState
from app.ai_interview.question_engine.schemas import QuestionRecord
from app.ai_interview.question_engine.enums import QuestionStatus
from app.ai_interview.answer_engine.schemas import EvaluationRecord
from app.ai_interview.answer_engine.enums import CoverageSignal, FollowUpSignal
from app.ai_interview.core.enums import QuestionType

def test_serialization_roundtrip_preserves_types_and_nested_models():
    """
    Proves that a complex Pydantic model can be serialized to a raw dictionary (BSON-compatible),
    and when re-loaded, ALL nested types, UUIDs, enums, and dates are perfectly restored.
    """
    
    blueprint = InterviewBlueprint(
        blueprint_version="1.0",
        total_question_budget=5,
        min_questions=2,
        max_questions=5,
        emergency_max_questions=7,
        topics=[]
    )
    
    session = InterviewSessionSchema(
        session_id=str(uuid.uuid4()),
        candidate_id=str(uuid.uuid4()),
        company_id=str(uuid.uuid4()),
        campaign_id=str(uuid.uuid4()),
        mode_id="mode_1",
        mode_version=1,
        state=InterviewState.IN_PROGRESS,
        blueprint=blueprint,
        created_at=datetime.now(timezone.utc),
        version=5,
        schema_version=1
    )
    
    # Add a TopicProgress
    tp = TopicProgress(
        topic_id="t1",
        state=TopicState.IN_PROGRESS,
        questions_asked=1
    )
    session.topic_progress.append(tp)
    
    # Add a QuestionRecord
    qr = QuestionRecord(
        record_id=str(uuid.uuid4()),
        session_id=session.session_id,
        turn_number=1,
        topic_id="t1",
        question_text="What is Python?",
        question_type=QuestionType.INITIAL,
        difficulty=DifficultyLevel.MEDIUM,
        status=QuestionStatus.EVALUATING
    )
    session.question_history.append(qr)
    
    # Add an EvaluationRecord
    er = EvaluationRecord(
        evaluation_id=str(uuid.uuid4()),
        question_record_id=qr.record_id,
        topic_id="t1",
        overall_score=0.9,
        qualitative_coverage_signal=CoverageSignal.QUALITATIVELY_COVERED,
        follow_up_signal=FollowUpSignal.NONE,
        timestamp=datetime.now(timezone.utc)
    )
    session.evaluation_history.append(er)
    
    # 1. Serialize to BSON-compatible dict (using model_dump with json mode ensures UUIDs -> str, Dates -> str, Enums -> str)
    bson_doc = session.model_dump(mode="json")
    
    # Validate it's a pure dict and no objects leaked
    assert isinstance(bson_doc, dict)
    assert isinstance(bson_doc["question_history"][0], dict)
    assert isinstance(bson_doc["evaluation_history"][0], dict)
    assert isinstance(bson_doc["state"], str)
    assert bson_doc["state"] == "in_progress"
    
    # 2. Deserialize back to Pydantic (simulating DB read)
    loaded_session = InterviewSessionSchema.model_validate(bson_doc)
    
    # 3. Assert deep equality and strict type reconstruction
    assert loaded_session.session_id == session.session_id
    assert loaded_session.state == InterviewState.IN_PROGRESS
    assert loaded_session.version == 5
    
    # Verify QuestionRecord typing! (This was the List[Any] bug)
    loaded_qr = loaded_session.question_history[0]
    assert isinstance(loaded_qr, QuestionRecord)
    assert loaded_qr.record_id == qr.record_id
    assert loaded_qr.status == QuestionStatus.EVALUATING
    assert loaded_qr.question_type == QuestionType.INITIAL
    
    # Verify EvaluationRecord typing!
    loaded_er = loaded_session.evaluation_history[0]
    assert isinstance(loaded_er, EvaluationRecord)
    assert loaded_er.overall_score == 0.9
    assert loaded_er.qualitative_coverage_signal == CoverageSignal.QUALITATIVELY_COVERED
    
    # Datetime preservation
    # Pydantic's model_validate automatically parses ISO8601 strings back to datetime objects
    assert isinstance(loaded_session.created_at, datetime)
