"""
Phase 9 — WebSocket Connection Manager
======================================
Ephemeral, in-memory registry mapping session_id to active WebSocket.
Enforces Single-Active-Connection policy: if a candidate reconnects,
the older socket is cleanly replaced and closed.
"""
import logging
from typing import Dict
from fastapi import WebSocket
from app.ai_interview.transport.schemas.ws_events import ConnectionReplacedEvent

logger = logging.getLogger("intellihire")

class InterviewConnectionManager:
    def __init__(self):
        # Maps session_id -> WebSocket
        self._connections: Dict[str, WebSocket] = {}

    async def register(self, session_id: str, websocket: WebSocket) -> None:
        """Register a new connection, replacing and closing any existing one."""
        existing = self._connections.get(session_id)
        if existing:
            try:
                event = ConnectionReplacedEvent(session_id=session_id)
                await existing.send_text(event.model_dump_json())
                await existing.close(code=4002, reason="Connection replaced")
            except Exception:
                pass  # Old socket might already be dead
        self._connections[session_id] = websocket

    def remove(self, session_id: str) -> None:
        """Remove a connection from the registry (on disconnect)."""
        self._connections.pop(session_id, None)

    async def send_event(self, session_id: str, event_json: str) -> bool:
        """Send a serialized JSON event to the session's active socket."""
        ws = self._connections.get(session_id)
        if ws is None:
            logger.warning({"event": "ws_send_no_connection", "session_id": session_id})
            return False
        
        try:
            await ws.send_text(event_json)
            return True
        except Exception as e:
            logger.warning({
                "event": "ws_send_failed", 
                "session_id": session_id,
                "error_type": type(e).__name__
            })
            self.remove(session_id)
            return False

# Global singleton
connection_manager = InterviewConnectionManager()
