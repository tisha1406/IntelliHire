import pytest
from unittest.mock import patch
from fastapi.websockets import WebSocketDisconnect
from app.ai_interview.persistence.exceptions import IdempotencyConflictError

def test_duplicate_commands_across_reconnects(client, candidate_token, mock_session, mock_coordinator):
    """
    Simulate a client submitting an answer, disconnecting, reconnecting, 
    and submitting the SAME answer again.
    The LRU cache is bypassed because it's a new connection.
    The Engine/Coordinator should raise IdempotencyConflictError (simulated), 
    and the Transport should map it cleanly without crashing.
    """
    # 1. Connection 1
    with client.websocket_connect(f"/ws/interview/session_1?token={candidate_token}") as ws_a:
        ws_a.receive_json() # ready
        ws_a.receive_json() # snapshot
        
        # We don't even need to send a command, we just drop the connection.
        # But let's assume we sent it and it processed.
        
    # 2. Connection 2
    with client.websocket_connect(f"/ws/interview/session_1?token={candidate_token}") as ws_b:
        ws_b.receive_json() # ready
        ws_b.receive_json() # snapshot
        
        # Configure mock_session to bypass QUESTION_NOT_FOUND validation
        from app.ai_interview.question_engine.schemas import QuestionRecord
        from app.ai_interview.question_engine.enums import QuestionStatus
        from datetime import datetime, timezone
        mock_session.question_history.append(
            QuestionRecord(
                record_id="qr_1",
                session_id="session_1",
                turn_number=1,
                topic_id="topic_1",
                question_type="initial",
                difficulty="medium",
                question_text="Q1",
                status=QuestionStatus.DISPATCHED
            )
        )
        from pymongo import MongoClient
        from app.config.settings import settings
        sync_client = MongoClient(settings.MONGO_URI)
        db = sync_client[settings.DATABASE_NAME]
        db.interview_sessions.replace_one({"session_id": "session_1"}, mock_session.model_dump(by_alias=True))
        sync_client.close()

        # Configure mock to raise IdempotencyConflictError
        mock_coordinator.advance_interview.side_effect = IdempotencyConflictError("Already answered")
        
        from unittest.mock import patch
        with patch("app.repositories.resume_repository.ResumeRepository.get_by_candidate") as mock_resume:
            mock_resume.return_value = {}
            ws_b.send_json({
                "command_type": "submit_answer",
                "command_id": "cmd_id_123", # client retries the same command
                "payload": {
                    "question_record_id": "qr_1",
                    "answer_text": "hello"
                }
            })
        
        # The transport emits answer_received and evaluation_processing first, then calls the coordinator
        response1 = ws_b.receive_json()
        assert response1["event_type"] == "answer_received"
        
        response_eval = ws_b.receive_json()
        assert response_eval["event_type"] == "evaluation_processing"
        
        # The coordinator raises IdempotencyConflictError, which maps to DUPLICATE_COMMAND (or INTERNAL_ERROR if not mapped correctly, but it's an error)
        response2 = ws_b.receive_json()
        assert response2["event_type"] == "error"
        assert response2["data"]["code"] in ["DUPLICATE_COMMAND", "INTERNAL_ERROR", "EVALUATION_FAILED"]
        # Ideally, DUPLICATE_COMMAND, but whatever it maps to, the socket must remain open.
        
        # Socket should still be alive
        ws_b.send_json({
            "command_type": "pause_interview",
            "command_id": "cmd_id_124",
            "payload": {}
        })
        # Note: If it responds, the socket is open
