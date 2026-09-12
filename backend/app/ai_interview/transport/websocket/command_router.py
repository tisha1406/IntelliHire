"""
Phase 9 — WebSocket Command Router
==================================
Parses raw JSON frames into typed WsCommand objects.
Enforces MAX_WS_MESSAGE_BYTES.
Applies LRU command deduplication.
"""
import json
from collections import OrderedDict
from typing import Dict
from pydantic import ValidationError

from app.config.settings import settings
from app.ai_interview.transport.schemas.ws_commands import WsCommand, WsCommandBase
from app.ai_interview.transport.exceptions import (
    WsPayloadTooLargeError,
    WsInvalidCommandError,
    WsDuplicateCommandError
)

class CommandDeduplicationCache:
    """
    Ephemeral LRU cache to prevent rapid double-taps of the same command_id.
    Note: Database guards (OCC, IdempotencyConflictError) provide the real safety;
    this is just an optimization.
    """
    def __init__(self, max_size: int = 50):
        # Maps session_id -> OrderedDict[command_id, bool]
        self._cache: Dict[str, OrderedDict[str, bool]] = {}
        self._max_size = max_size

    def is_duplicate(self, session_id: str, command_id: str) -> bool:
        session_cache = self._cache.setdefault(session_id, OrderedDict())
        if command_id in session_cache:
            return True
            
        session_cache[command_id] = True
        if len(session_cache) > self._max_size:
            session_cache.popitem(last=False)
        return False

    def cleanup(self, session_id: str) -> None:
        self._cache.pop(session_id, None)


class CommandRouter:
    def __init__(self):
        self._dedup = CommandDeduplicationCache()

    def parse(self, session_id: str, raw_text: str) -> WsCommandBase:
        """
        Parse raw text into a typed WsCommand.
        Raises WsCommandError variants on failure.
        """
        # Guard 1: Frame size
        if len(raw_text.encode('utf-8')) > settings.MAX_WS_MESSAGE_BYTES:
            raise WsPayloadTooLargeError("Message exceeds maximum size")

        # Guard 2: Valid JSON
        try:
            data = json.loads(raw_text)
        except json.JSONDecodeError:
            raise WsInvalidCommandError("Malformed JSON")

        if not isinstance(data, dict):
            raise WsInvalidCommandError("Command must be a JSON object")

        # Extract command_id for dedup check (requires manual check before Pydantic parsing)
        command_id = data.get("command_id")
        if not command_id or not isinstance(command_id, str):
            raise WsInvalidCommandError("Missing or invalid command_id")

        # Guard 3: Deduplication
        if self._dedup.is_duplicate(session_id, command_id):
            raise WsDuplicateCommandError(f"Duplicate command_id: {command_id}")

        # Guard 4: Schema validation (discriminator matches command_type)
        try:
            # We use TypeAdapter to parse the discriminated union, but since we defined
            # WsCommand as an Annotated Union, we can just use TypeAdapter(WsCommand).validate_python
            from pydantic import TypeAdapter
            adapter = TypeAdapter(WsCommand)
            command = adapter.validate_python(data)
            return command
        except ValidationError:
            # We don't leak the exact Pydantic schema validation errors to the client
            # to avoid leaking internals, but we could log it.
            raise WsInvalidCommandError("Invalid command schema or unknown command_type")

    def cleanup_session(self, session_id: str) -> None:
        self._dedup.cleanup(session_id)

command_router = CommandRouter()
