"""
Phase 9 — Typed WebSocket Command Schemas (Client → Server)
=============================================================
Every message from the client must conform to one of these schemas.

Design rules:
- ``command_type`` is the discriminator field for Pydantic's Union parsing.
- ``command_id`` is a client-generated UUID used for deduplication and
  correlation (it appears in error events and acknowledgements).
- Payloads carry only what is strictly needed; the server derives everything
  else from the authenticated session context.
- ``answer_text`` is NOT logged anywhere.  It flows directly into AnswerSubmission
  which is passed to the synchronous engine layer.
"""
from __future__ import annotations

import uuid
from typing import Annotated, Literal, Optional, Union

from pydantic import BaseModel, Field, field_validator


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Transport-level guards (also stored in settings, but used here for Pydantic validation)
MAX_ANSWER_TEXT_CHARS: int = 8_000
MAX_WS_MESSAGE_BYTES: int = 32_768


# ---------------------------------------------------------------------------
# Base command
# ---------------------------------------------------------------------------

class WsCommandBase(BaseModel):
    """Common envelope fields present on every client → server message."""
    command_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Client-generated UUID. Used for deduplication and error correlation.",
    )
    command_type: str


# ---------------------------------------------------------------------------
# start_interview
# ---------------------------------------------------------------------------

class StartInterviewPayload(BaseModel):
    """No payload fields required; all context is derived from the session."""
    pass


class StartInterviewCommand(WsCommandBase):
    command_type: Literal["start_interview"]
    payload: StartInterviewPayload = Field(default_factory=StartInterviewPayload)


# ---------------------------------------------------------------------------
# submit_answer
# ---------------------------------------------------------------------------

class SubmitAnswerPayload(BaseModel):
    question_record_id: str = Field(
        description="The record_id of the QuestionRecord this answer corresponds to."
    )
    answer_text: str = Field(
        description="Candidate's typed answer. Not logged. Max 8000 chars.",
    )

    @field_validator("answer_text")
    @classmethod
    def _validate_answer_length(cls, v: str) -> str:
        if len(v) > MAX_ANSWER_TEXT_CHARS:
            raise ValueError(
                f"answer_text exceeds maximum length of {MAX_ANSWER_TEXT_CHARS} characters."
            )
        return v


class SubmitAnswerCommand(WsCommandBase):
    command_type: Literal["submit_answer"]
    payload: SubmitAnswerPayload


# ---------------------------------------------------------------------------
# pause_interview
# ---------------------------------------------------------------------------

class PauseInterviewPayload(BaseModel):
    pass


class PauseInterviewCommand(WsCommandBase):
    command_type: Literal["pause_interview"]
    payload: PauseInterviewPayload = Field(default_factory=PauseInterviewPayload)


# ---------------------------------------------------------------------------
# resume_interview
# ---------------------------------------------------------------------------

class ResumeInterviewPayload(BaseModel):
    pass


class ResumeInterviewCommand(WsCommandBase):
    command_type: Literal["resume_interview"]
    payload: ResumeInterviewPayload = Field(default_factory=ResumeInterviewPayload)


# ---------------------------------------------------------------------------
# ping
# ---------------------------------------------------------------------------

class PingCommand(WsCommandBase):
    command_type: Literal["ping"]
    payload: Optional[dict] = None


# ---------------------------------------------------------------------------
# Discriminated union — the single parse target
# ---------------------------------------------------------------------------

WsCommand = Annotated[
    Union[
        StartInterviewCommand,
        SubmitAnswerCommand,
        PauseInterviewCommand,
        ResumeInterviewCommand,
        PingCommand,
    ],
    Field(discriminator="command_type"),
]
