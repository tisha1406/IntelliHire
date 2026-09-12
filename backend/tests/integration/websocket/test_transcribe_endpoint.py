import pytest
from fastapi.testclient import TestClient
from pymongo import MongoClient
import io
import datetime

from app.config.settings import settings
from app.ai_interview.schemas.session import InterviewSessionSchema
from app.ai_interview.core.enums import InterviewState
from app.ai_interview.question_engine.schemas import QuestionStatus, QuestionRecord

@pytest.fixture
def mock_session_transcribe():
    return InterviewSessionSchema(
        session_id="session_transcribe",
        candidate_id="cand_1",
        company_id="comp_1",
        campaign_id="camp_1",
        mode_id="mode_1",
        mode_version=1,
            blueprint={
                "blueprint_version": "1",
                "total_question_budget": 5,
                "min_questions": 1,
                "max_questions": 5,
                "emergency_max_questions": 6,
                "topics": []
            },
        created_at=datetime.datetime.now(datetime.timezone.utc),
        state=InterviewState.IN_PROGRESS,
        budget={"max_questions": 5, "max_duration_minutes": 30},
        question_history=[
            QuestionRecord(
                record_id="q_1",
                session_id="session_transcribe",
                turn_number=1,
                topic_id="topic_1",
                question_type="initial",
                difficulty="medium",
                question_text="Q1?",
                status=QuestionStatus.DISPATCHED
            )
        ]
    )

def test_transcribe_unauthenticated(client):
    response = client.post("/api/interview/sessions/sess/questions/q1/transcribe", data={"transcription_request_id": "req_1"}, files={"file": ("a.webm", b"audio", "audio/webm")})
    assert response.status_code in [401, 403]

def test_transcribe_success_mock(client, candidate_token, mock_session_transcribe, monkeypatch):
    # Insert session
    sync_client = MongoClient(settings.MONGO_URI)
    db = sync_client[settings.DATABASE_NAME]
    db.interview_sessions.replace_one(
        {"session_id": "session_transcribe"}, 
        mock_session_transcribe.model_dump(by_alias=True), 
        upsert=True
    )
    sync_client.close()
    
    # Mock the STT Provider
    from app.ai_interview.speech_infrastructure import TranscriptionResult
    async def mock_transcribe(*args, **kwargs):
        return TranscriptionResult(transcript="Mock transcript", duration_ms=1500, provider="mock")
        
    monkeypatch.setattr("app.ai_interview.speech_infrastructure.stt.sarvam_saaras_adapter.SarvamSaarasAdapter.transcribe", mock_transcribe)

    audio_data = b"fake audio data"
    files = {"file": ("audio.webm", audio_data, "audio/webm")}
    data = {"transcription_request_id": "req_1"}
    
    response = client.post(
        f"/api/interview/sessions/session_transcribe/questions/q_1/transcribe",
        headers={"Authorization": f"Bearer {candidate_token}"},
        files=files,
        data=data
    )
    
    assert response.status_code == 200
    res_data = response.json()
    assert res_data["transcript"] == "Mock transcript"
    assert res_data["question_record_id"] == "q_1"
    assert res_data["transcription_request_id"] == "req_1"

def test_transcribe_wrong_question_correlation(client, candidate_token, mock_session_transcribe):
    # Insert session
    sync_client = MongoClient(settings.MONGO_URI)
    db = sync_client[settings.DATABASE_NAME]
    db.interview_sessions.replace_one(
        {"session_id": "session_transcribe"}, 
        mock_session_transcribe.model_dump(by_alias=True), 
        upsert=True
    )
    sync_client.close()
    
    audio_data = b"fake audio data"
    files = {"file": ("audio.webm", audio_data, "audio/webm")}
    data = {"transcription_request_id": "req_1"}
    
    # Sending q_wrong instead of q_1
    response = client.post(
        f"/api/interview/sessions/session_transcribe/questions/q_wrong/transcribe",
        headers={"Authorization": f"Bearer {candidate_token}"},
        files=files,
        data=data
    )
    
    # HTTP 400 Bad Request because of strict correlation failure
    assert response.status_code == 400
    assert "Question is not currently answerable" in response.text
