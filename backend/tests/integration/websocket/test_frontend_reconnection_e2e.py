import pytest
from datetime import datetime, timezone
from pymongo import MongoClient

from app.config.settings import settings
from app.ai_interview.question_engine.schemas import QuestionRecord
from app.ai_interview.question_engine.enums import QuestionStatus
from app.ai_interview.schemas.session import InterviewState

def test_reconnect_during_unanswered_question(client, candidate_token, mock_session):
    """
    Scenario A: Disconnect while unanswered question is displayed.
    Expected: Reconnect returns authoritative SessionSnapshot. Same unresolved question is restored.
    """
    # 1. Setup session with an unanswered question in the actual DB
    mock_session.state = InterviewState.IN_PROGRESS
    mock_session.question_history.append(
        QuestionRecord(
            record_id="qr_1",
            session_id="session_1",
            turn_number=1,
            topic_id="topic_1",
            question_type="initial",
            difficulty="medium",
            question_text="What is Python?",
            status=QuestionStatus.DISPATCHED
        )
    )
    
    sync_client = MongoClient(settings.MONGO_URI)
    db = sync_client[settings.DATABASE_NAME]
    db.interview_sessions.replace_one({"session_id": "session_1"}, mock_session.model_dump(by_alias=True))
    sync_client.close()

    # 2. Connect via WS and verify snapshot
    with client.websocket_connect(f"/ws/interview/session_1?token={candidate_token}") as ws:
        # 1. Connection established
        ready = ws.receive_json()
        assert ready["event_type"] == "connection_ready"
        
        # 2. Receive Snapshot
        snapshot = ws.receive_json()
        assert snapshot["event_type"] == "session_snapshot"
        data = snapshot["data"]
        
        # 3. Assertions
        assert data["interview_state"] == "in_progress"
        assert "current_question" in data
        assert data["current_question"]["status"] == "dispatched"
        assert data["current_question"]["question_text"] == "What is Python?"

def test_reconnect_after_terminal_state(client, candidate_token, mock_session):
    """
    Scenario F: Browser refresh after terminal completion.
    Expected: SessionSnapshot indicates terminal state. No unanswered question is emitted.
    """
    # 1. Setup completed session
    mock_session.state = InterviewState.COMPLETED
    
    sync_client = MongoClient(settings.MONGO_URI)
    db = sync_client[settings.DATABASE_NAME]
    db.interview_sessions.replace_one({"session_id": "session_1"}, mock_session.model_dump(by_alias=True))
    sync_client.close()

    # 2. Connect via WS
    with client.websocket_connect(f"/ws/interview/session_1?token={candidate_token}") as ws:
        ready = ws.receive_json()
        assert ready["event_type"] == "connection_ready"
        
        snapshot = ws.receive_json()
        assert snapshot["event_type"] == "session_snapshot"
        data = snapshot["data"]
        
        # 3. Assertions
        assert data["interview_state"] == "completed"
        assert data["is_completed"] is True


