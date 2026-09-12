"""
Phase 9 — Transport-Layer Typed Exceptions
==========================================
These exceptions model transport-level failures distinct from engine failures.

Hierarchy:
    TransportError
    ├── WsAuthError            — JWT / identity failure (close 4001/4003/4004)
    ├── WsCommandError
    │   ├── WsPayloadTooLargeError
    │   ├── WsInvalidCommandError
    │   └── WsDuplicateCommandError
    └── WsSessionError         — session-level precondition violations
"""


class TransportError(Exception):
    """Base class for all Phase 9 transport exceptions."""


# ---------------------------------------------------------------------------
# Authentication / Authorization
# ---------------------------------------------------------------------------

class WsAuthError(TransportError):
    """
    Raised when a WebSocket connection cannot be authenticated or authorized.

    Carries a ws_close_code that the endpoint uses when closing the socket.
    """

    def __init__(self, message: str, ws_close_code: int = 4001) -> None:
        super().__init__(message)
        self.ws_close_code = ws_close_code


# ---------------------------------------------------------------------------
# Command parsing / routing
# ---------------------------------------------------------------------------

class WsCommandError(TransportError):
    """Base class for command-level transport failures."""


class WsPayloadTooLargeError(WsCommandError):
    """Raw WebSocket frame exceeds MAX_WS_MESSAGE_BYTES."""


class WsInvalidCommandError(WsCommandError):
    """JSON is malformed, schema validation failed, or command type is unknown."""


class WsDuplicateCommandError(WsCommandError):
    """Command id matches a recently processed command (transport-level dedup hit)."""


# ---------------------------------------------------------------------------
# Session preconditions
# ---------------------------------------------------------------------------

class WsSessionError(TransportError):
    """
    Raised when a command is valid but the session is not in a state that
    permits it (e.g. submitting an answer to a completed session).
    """
