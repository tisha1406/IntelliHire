import pytest
from fastapi.websockets import WebSocketDisconnect

def test_submit_answer_before_start_rejected(client, candidate_token, mock_session, mock_coordinator):
    """
    If a client attempts to submit an answer for a non-existent question or 
    before starting the interview, it should be rejected gracefully by the transport layer 
    (which maps to INVALID_SESSION_STATE).
    """
    with client.websocket_connect(f"/ws/interview/session_1?token={candidate_token}") as websocket:
        # 1. Connection Ready
        data = websocket.receive_json()
        assert data["event_type"] == "connection_ready"
        
        # 2. Session Snapshot
        data = websocket.receive_json()
        assert data["event_type"] == "session_snapshot"
        
        # 3. Send invalid command
        websocket.send_json({
            "command_type": "submit_answer",
            "command_id": "cmd_1",
            "payload": {
                "question_record_id": "invalid_qr",
                "answer_text": "hello"
            }
        })
        
        # 4. We should receive an error event
        response = websocket.receive_json()
        assert response["event_type"] == "error"
        # The runtime will reject this since 'invalid_qr' doesn't match the current question (which is None)
        # Depending on how the error is mapped, it should be a 400x logic error.
        assert response["data"]["code"] in ["INVALID_SESSION_STATE", "QUESTION_NOT_FOUND"]
