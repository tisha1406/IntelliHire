"""
Phase 9 — WebSocket Error Codes & Payloads
==========================================
Machine-readable error codes sent to the client as ``error`` events.

Rules:
- Codes are human-readable enum strings (not numeric HTTP codes).
- No Python tracebacks, API keys, prompts, or JWT tokens must ever appear in
  ``message`` or any other field.
- ``retryable`` guides the client: True means "send the same command again
  (possibly after a short wait)"; False means "this command cannot succeed
  without a different state or a new connection."
"""
from __future__ import annotations

from enum import Enum
from typing import Optional
from pydantic import BaseModel


class WsErrorCode(str, Enum):
    # ------------------------------------------------------------------
    # Authentication & Authorization (connection-level)
    # ------------------------------------------------------------------
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"

    # ------------------------------------------------------------------
    # Session lookup
    # ------------------------------------------------------------------
    SESSION_NOT_FOUND = "SESSION_NOT_FOUND"

    # ------------------------------------------------------------------
    # Session-state preconditions
    # ------------------------------------------------------------------
    INVALID_SESSION_STATE = "INVALID_SESSION_STATE"
    SESSION_TERMINAL = "SESSION_TERMINAL"

    # ------------------------------------------------------------------
    # Command parsing
    # ------------------------------------------------------------------
    INVALID_COMMAND = "INVALID_COMMAND"
    INVALID_PAYLOAD = "INVALID_PAYLOAD"
    PAYLOAD_TOO_LARGE = "PAYLOAD_TOO_LARGE"
    DUPLICATE_COMMAND = "DUPLICATE_COMMAND"

    # ------------------------------------------------------------------
    # Question lifecycle
    # ------------------------------------------------------------------
    QUESTION_NOT_FOUND = "QUESTION_NOT_FOUND"
    QUESTION_STATUS_CONFLICT = "QUESTION_STATUS_CONFLICT"

    # ------------------------------------------------------------------
    # Concurrency / lease
    # ------------------------------------------------------------------
    CLAIM_ALREADY_HELD = "CLAIM_ALREADY_HELD"
    EVALUATION_IN_PROGRESS = "EVALUATION_IN_PROGRESS"
    GENERATION_IN_PROGRESS = "GENERATION_IN_PROGRESS"
    CONCURRENCY_CONFLICT = "CONCURRENCY_CONFLICT"
    FENCING_CONFLICT = "FENCING_CONFLICT"
    IDEMPOTENCY_CONFLICT = "IDEMPOTENCY_CONFLICT"

    # ------------------------------------------------------------------
    # Engine failures (safe, non-leaking descriptions)
    # ------------------------------------------------------------------
    GENERATION_FAILED = "GENERATION_FAILED"
    EVALUATION_FAILED = "EVALUATION_FAILED"
    PERSISTENCE_FAILED = "PERSISTENCE_FAILED"
    INTERNAL_ERROR = "INTERNAL_ERROR"


class WsErrorPayload(BaseModel):
    """
    Typed error payload sent inside an ``error`` event.

    Never include raw exception messages, stack traces, or sensitive data.
    """
    code: WsErrorCode
    message: str          # Safe, human-readable, client-displayable
    retryable: bool
    command_id: Optional[str] = None   # Echo the triggering command_id when available


# ------------------------------------------------------------------
# Safe default messages per error code
# ------------------------------------------------------------------
_SAFE_MESSAGES: dict[WsErrorCode, str] = {
    WsErrorCode.UNAUTHORIZED: "Authentication failed. Please reconnect with a valid token.",
    WsErrorCode.FORBIDDEN: "You are not authorized to access this interview session.",
    WsErrorCode.SESSION_NOT_FOUND: "Interview session not found.",
    WsErrorCode.INVALID_SESSION_STATE: "This action is not permitted in the current session state.",
    WsErrorCode.SESSION_TERMINAL: "This interview session has already ended.",
    WsErrorCode.INVALID_COMMAND: "The command could not be parsed or is not recognised.",
    WsErrorCode.INVALID_PAYLOAD: "The command payload is invalid.",
    WsErrorCode.PAYLOAD_TOO_LARGE: "The message exceeds the maximum allowed size.",
    WsErrorCode.DUPLICATE_COMMAND: "This command has already been processed.",
    WsErrorCode.QUESTION_NOT_FOUND: "The referenced question was not found in this session.",
    WsErrorCode.QUESTION_STATUS_CONFLICT: "The question has already been answered and evaluated.",
    WsErrorCode.CLAIM_ALREADY_HELD: "Another operation is in progress. Please wait and retry.",
    WsErrorCode.EVALUATION_IN_PROGRESS: "Your answer is already being evaluated.",
    WsErrorCode.GENERATION_IN_PROGRESS: "A question is currently being generated. Please wait.",
    WsErrorCode.CONCURRENCY_CONFLICT: "A concurrent update conflict occurred. Please retry.",
    WsErrorCode.FENCING_CONFLICT: "This operation was superseded by a newer request.",
    WsErrorCode.IDEMPOTENCY_CONFLICT: "This operation has already been completed.",
    WsErrorCode.GENERATION_FAILED: "Question generation failed. The interview could not continue.",
    WsErrorCode.EVALUATION_FAILED: "Answer evaluation failed. Please try resubmitting.",
    WsErrorCode.PERSISTENCE_FAILED: "A storage error occurred. Your progress has been preserved. Please reconnect.",
    WsErrorCode.INTERNAL_ERROR: "An unexpected internal error occurred.",
}

# Error codes for which the client should retry the same command
_RETRYABLE_CODES: frozenset[WsErrorCode] = frozenset({
    WsErrorCode.CLAIM_ALREADY_HELD,
    WsErrorCode.EVALUATION_IN_PROGRESS,
    WsErrorCode.GENERATION_IN_PROGRESS,
    WsErrorCode.CONCURRENCY_CONFLICT,
    WsErrorCode.EVALUATION_FAILED,     # retryable: client can re-submit
    WsErrorCode.PERSISTENCE_FAILED,
})


def build_error_payload(
    code: WsErrorCode,
    command_id: Optional[str] = None,
    override_message: Optional[str] = None,
) -> WsErrorPayload:
    """
    Build a safe WsErrorPayload for the given error code.

    ``override_message`` allows callers to provide a more specific safe
    message, e.g. distinguishing which question was not found, without
    leaking any internal details.
    """
    return WsErrorPayload(
        code=code,
        message=override_message or _SAFE_MESSAGES.get(code, "An error occurred."),
        retryable=code in _RETRYABLE_CODES,
        command_id=command_id,
    )
