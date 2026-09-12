import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi import WebSocket
from jose import jwt

from app.config.settings import settings
from app.ai_interview.transport.websocket.authenticator import authenticate_ws, WsConnectionContext
from app.ai_interview.persistence.exceptions import SessionNotFoundError
from app.ai_interview.schemas.session import InterviewSessionSchema
from app.ai_interview.core.enums import InterviewState
from app.rbac.models import UserRole

from app.auth.jwt_handler import create_access_token

@pytest.fixture
def mock_websocket():
    ws = MagicMock(spec=WebSocket)
    ws.close = AsyncMock()
    return ws

@pytest.fixture
def mock_repo():
    repo = AsyncMock()
    from datetime import datetime, timezone
    # By default, mock successful lookup
    session = InterviewSessionSchema(
        session_id="session_1",
        candidate_id="cand_1",
        company_id="comp_1",
        campaign_id="camp_1",
        mode_id="mode_1",
        mode_version=1,
        state=InterviewState.IN_PROGRESS,
        blueprint={
            "blueprint_version": "1.0",
            "topics": [], 
            "total_question_budget": 5, 
            "min_questions": 3,
            "max_questions": 7,
            "emergency_max_questions": 10
        },
        created_at=datetime.now(timezone.utc)
    )
    repo.get_by_id.return_value = session
    return repo

@pytest.mark.asyncio
async def test_missing_token(mock_websocket, mock_repo):
    mock_websocket.query_params = {}
    
    result = await authenticate_ws(mock_websocket, "session_1", mock_repo)
    assert result is None
    mock_websocket.close.assert_called_once_with(code=4001, reason="Missing token")

@pytest.mark.asyncio
async def test_invalid_token(mock_websocket, mock_repo):
    mock_websocket.query_params = {"token": "invalid_jwt_string"}
    
    result = await authenticate_ws(mock_websocket, "session_1", mock_repo)
    assert result is None
    mock_websocket.close.assert_called_once_with(code=4001, reason="Invalid or expired token")

@pytest.mark.asyncio
async def test_role_mismatch(mock_websocket, mock_repo):
    jwt_str = create_access_token(user_id="user_1", role=UserRole.COMPANY.value)
    mock_websocket.query_params = {"token": jwt_str}
    
    result = await authenticate_ws(mock_websocket, "session_1", mock_repo)
    assert result is None
    mock_websocket.close.assert_called_once_with(code=4001, reason="Invalid role")

@pytest.mark.asyncio
async def test_missing_candidate_id(mock_websocket, mock_repo):
    jwt_str = create_access_token(user_id="cand_1", role=UserRole.CANDIDATE.value)
    mock_websocket.query_params = {"token": jwt_str}
    
    result = await authenticate_ws(mock_websocket, "session_1", mock_repo)
    assert result is None
    mock_websocket.close.assert_called_once_with(code=4001, reason="Missing candidate_id")

@pytest.mark.asyncio
async def test_session_not_found(mock_websocket, mock_repo):
    jwt_str = create_access_token(user_id="cand_1", role=UserRole.CANDIDATE.value, candidate_id="cand_1", company_id="comp_1")
    mock_websocket.query_params = {"token": jwt_str}
    
    mock_repo.get_by_id.side_effect = SessionNotFoundError("Not found")
    
    result = await authenticate_ws(mock_websocket, "session_1", mock_repo)
    assert result is None
    mock_websocket.close.assert_called_once_with(code=4004, reason="Session not found")

@pytest.mark.asyncio
async def test_ownership_mismatch(mock_websocket, mock_repo):
    jwt_str = create_access_token(user_id="cand_2", role=UserRole.CANDIDATE.value, candidate_id="cand_2", company_id="comp_1")
    mock_websocket.query_params = {"token": jwt_str}
    
    result = await authenticate_ws(mock_websocket, "session_1", mock_repo)
    assert result is None
    mock_websocket.close.assert_called_once_with(code=4003, reason="Forbidden")

@pytest.mark.asyncio
async def test_successful_auth(mock_websocket, mock_repo):
    jwt_str = create_access_token(user_id="cand_1", role=UserRole.CANDIDATE.value, candidate_id="cand_1", company_id="comp_1")
    mock_websocket.query_params = {"token": jwt_str}
    
    result = await authenticate_ws(mock_websocket, "session_1", mock_repo)
    
    assert result is not None
    assert isinstance(result, WsConnectionContext)
    assert result.token.candidate_id == "cand_1"
    assert result.session.session_id == "session_1"
    mock_websocket.close.assert_not_called()
