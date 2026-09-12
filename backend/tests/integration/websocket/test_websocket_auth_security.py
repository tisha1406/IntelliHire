import pytest
from fastapi.websockets import WebSocketDisconnect
from jose import jwt
from app.config.settings import settings
from app.rbac.models import UserRole


def test_auth_security_invalid_token(client, mock_session):
    # Missing token entirely
    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect(f"/ws/interview/session_1"):
            pass
    
    # Invalid token string
    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect(f"/ws/interview/session_1?token=invalid_string"):
            pass

def test_auth_security_role_mismatch(client, mock_session):
    from datetime import datetime, timedelta, timezone
    payload = {
        "sub": "user_1", 
        "role": UserRole.COMPANY.value,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=60),
        "iat": datetime.now(timezone.utc)
    }
    jwt_str = jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    
    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect(f"/ws/interview/session_1?token={jwt_str}"):
            pass

def test_auth_security_ownership_mismatch(client, other_candidate_token, mock_session):
    # Valid token, but for cand_2, not cand_1 (who owns session_1)
    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect(f"/ws/interview/session_1?token={other_candidate_token}"):
            pass

def test_auth_security_session_not_found(client, candidate_token):
    # Session 999 doesn't exist in mock DB
    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect(f"/ws/interview/session_999?token={candidate_token}"):
            pass
