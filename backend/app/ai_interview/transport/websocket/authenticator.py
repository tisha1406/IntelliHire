"""
Phase 9 — WebSocket Authenticator
=================================
Validates JWT tokens extracted from the WebSocket upgrade query string.
Validates candidate role and session ownership.

Does NOT use FastAPI Depends(HTTPBearer()) as that relies on Authorization headers
which are poorly supported in browser WebSocket APIs.
"""
from dataclasses import dataclass
from typing import Optional
from fastapi import WebSocket
from jose import jwt, JWTError

from app.config.settings import settings
from app.auth.jwt_handler import TokenPayload
from app.ai_interview.persistence.repository import InterviewSessionRepository
from app.ai_interview.persistence.exceptions import SessionNotFoundError
from app.ai_interview.schemas.session import InterviewSessionSchema

@dataclass
class WsConnectionContext:
    token: TokenPayload
    session: InterviewSessionSchema

async def authenticate_ws(
    websocket: WebSocket,
    session_id: str,
    repo: InterviewSessionRepository,
) -> Optional[WsConnectionContext]:
    """
    Authenticate and authorize a WebSocket connection.
    If validation fails, closes the socket with a 400X code and returns None.
    Does NOT log the token.
    """
    token_str = websocket.query_params.get("token")
    if not token_str:
        await websocket.close(code=4001, reason="Missing token")
        return None

    try:
        payload = jwt.decode(
            token_str,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM]
        )
        token = TokenPayload(**payload)
    except JWTError:
        await websocket.close(code=4001, reason="Invalid or expired token")
        return None

    # Must be candidate
    if token.role.upper() != "CANDIDATE":
        await websocket.close(code=4001, reason="Invalid role")
        return None

    if not token.candidate_id:
        await websocket.close(code=4001, reason="Missing candidate_id")
        return None

    # Load session and verify ownership
    try:
        session = await repo.get_by_id(session_id)
    except SessionNotFoundError:
        await websocket.close(code=4004, reason="Session not found")
        return None

    if session.candidate_id != token.candidate_id:
        await websocket.close(code=4003, reason="Forbidden")
        return None

    return WsConnectionContext(token=token, session=session)
