import pytest
import json
from app.ai_interview.transport.websocket.command_router import CommandRouter, CommandDeduplicationCache
from app.ai_interview.transport.exceptions import (
    WsPayloadTooLargeError, WsInvalidCommandError, WsDuplicateCommandError
)
from app.config.settings import settings
from app.ai_interview.transport.schemas.ws_commands import SubmitAnswerCommand

@pytest.fixture
def router():
    return CommandRouter()

def test_max_ws_message_bytes_rejection(router, monkeypatch):
    monkeypatch.setattr(settings, "MAX_WS_MESSAGE_BYTES", 50)
    
    # 51 bytes
    large_payload = 'a' * 51 
    with pytest.raises(WsPayloadTooLargeError):
        router.parse("session_123", large_payload)

def test_malformed_json_rejection(router):
    bad_json = '{"command_type": "submit_answer", "command_id": "123"' # Missing closing brace
    with pytest.raises(WsInvalidCommandError, match="Malformed JSON"):
        router.parse("session_123", bad_json)

def test_invalid_command_id(router):
    bad_json = '{"command_type": "submit_answer"}'
    with pytest.raises(WsInvalidCommandError, match="Missing or invalid command_id"):
        router.parse("session_123", bad_json)

def test_invalid_command_schema(router):
    # Valid JSON, but missing payload for submit_answer
    data = json.dumps({"command_type": "submit_answer", "command_id": "cmd_123"})
    with pytest.raises(WsInvalidCommandError, match="Invalid command schema or unknown command_type"):
        router.parse("session_123", data)

def test_unknown_command_type(router):
    data = json.dumps({"command_type": "explode", "command_id": "cmd_123"})
    with pytest.raises(WsInvalidCommandError, match="Invalid command schema or unknown command_type"):
        router.parse("session_123", data)

def test_lru_deduplication(router):
    data = json.dumps({
        "command_type": "submit_answer",
        "command_id": "cmd_dedup_1",
        "payload": {
            "question_record_id": "q1",
            "answer_text": "My answer"
        }
    })
    
    # First parse should succeed
    command = router.parse("session_123", data)
    assert isinstance(command, SubmitAnswerCommand)
    
    # Second parse with SAME command_id in SAME session should fail
    with pytest.raises(WsDuplicateCommandError):
        router.parse("session_123", data)
        
    # Same command in DIFFERENT session should succeed
    command2 = router.parse("session_456", data)
    assert isinstance(command2, SubmitAnswerCommand)

def test_lru_eviction(router):
    router._dedup = CommandDeduplicationCache(max_size=2)
    
    cmd_template = {
        "command_type": "submit_answer",
        "payload": {"question_record_id": "q1", "answer_text": "ans"}
    }
    
    # Add cmd_1
    cmd_template["command_id"] = "cmd_1"
    router.parse("session_1", json.dumps(cmd_template))
    
    # Add cmd_2
    cmd_template["command_id"] = "cmd_2"
    router.parse("session_1", json.dumps(cmd_template))
    
    # Add cmd_3 (should evict cmd_1)
    cmd_template["command_id"] = "cmd_3"
    router.parse("session_1", json.dumps(cmd_template))
    
    # Now cmd_1 should not be considered duplicate by LRU anymore
    cmd_template["command_id"] = "cmd_1"
    command = router.parse("session_1", json.dumps(cmd_template))
    assert command.command_id == "cmd_1"
