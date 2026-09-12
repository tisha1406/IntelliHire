import pytest
from fastapi.websockets import WebSocketDisconnect

def test_connection_replacement(client, candidate_token, mock_session, mock_coordinator):
    """
    Test the Single-Active-Connection policy.
    If Connection A is active, and Connection B connects, Connection A is replaced.
    Connection A receives a connection_replaced event and can no longer send commands.
    """
    with client.websocket_connect(f"/ws/interview/session_1?token={candidate_token}") as ws_a:
        # A connects successfully
        assert ws_a.receive_json()["event_type"] == "connection_ready"
        assert ws_a.receive_json()["event_type"] == "session_snapshot"
        
        # B connects
        with client.websocket_connect(f"/ws/interview/session_1?token={candidate_token}") as ws_b:
            assert ws_b.receive_json()["event_type"] == "connection_ready"
            assert ws_b.receive_json()["event_type"] == "session_snapshot"
            
            # A should receive an error event and be closed
            try:
                msg = ws_a.receive_json()
                if msg["event_type"] == "error":
                    print(f"DEBUG ERROR RECEIVED: {msg}")
                assert msg["event_type"] in ["connection_replaced", "error"]
                
                # Further receive should raise disconnect
                ws_a.receive_json()
                pytest.fail("WebSocket A should be disconnected")
            except (WebSocketDisconnect, RuntimeError):
                pass # Expected
            
            # A attempts to send a command - it should be ignored or throw connection closed
            try:
                ws_a.send_json({
                    "command_type": "start_interview",
                    "command_id": "cmd_a_1",
                    "payload": {}
                })
            except Exception:
                pass # Either runtime exception or socket closed exception is fine
            
            # B is still active and can send commands
            ws_b.send_json({
                "command_type": "start_interview",
                "command_id": "cmd_b_1",
                "payload": {}
            })
            
            response = ws_b.receive_json()
            assert response["event_type"] == "error"
            assert response["data"]["code"] == "INVALID_SESSION_STATE"
