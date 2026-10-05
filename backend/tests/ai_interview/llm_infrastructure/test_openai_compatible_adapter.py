import pytest
import httpx
from pydantic import BaseModel
from app.ai_interview.llm_infrastructure.adapters.openai_adapter import OpenAICompatibleAdapter
from app.ai_interview.llm_infrastructure.exceptions import (
    LLMFatalError, LLMTransientError, LLMValidationError
)

class DummyResponse(BaseModel):
    value: int

class MockElapsed:
    def total_seconds(self):
        return 0.1

class MockResponse:
    def __init__(self, status_code, json_data=None, text=""):
        self.status_code = status_code
        self._json_data = json_data
        self.text = text
        self.elapsed = MockElapsed()
        
    def raise_for_status(self):
        if self.status_code >= 400:
            raise httpx.HTTPStatusError("error", request=httpx.Request("POST", ""), response=self)
            
    def json(self):
        return self._json_data


def test_openai_adapter_transient_error(monkeypatch):
    adapter = OpenAICompatibleAdapter(api_key="test")
    
    def mock_post(*args, **kwargs):
        return MockResponse(500, text="Internal Server Error")
        
    monkeypatch.setattr(httpx.Client, "post", mock_post)
    
    with pytest.raises(LLMTransientError, match="Transient provider error: 500 - Internal Server Error"):
        adapter.generate_structured("sys", "user", DummyResponse)


def test_openai_adapter_fatal_error(monkeypatch):
    adapter = OpenAICompatibleAdapter(api_key="test")
    
    def mock_post(*args, **kwargs):
        return MockResponse(400, text="{\"error\": {\"message\": \"Invalid schema\"}}")
        
    monkeypatch.setattr(httpx.Client, "post", mock_post)
    
    with pytest.raises(LLMFatalError, match='Fatal provider error: 400 - {"error": {"message": "Invalid schema"}}'):
        adapter.generate_structured("sys", "user", DummyResponse)


def test_openai_adapter_fatal_error_truncation(monkeypatch):
    adapter = OpenAICompatibleAdapter(api_key="test")
    
    long_error = "x" * 600
    
    def mock_post(*args, **kwargs):
        return MockResponse(400, text=long_error)
        
    monkeypatch.setattr(httpx.Client, "post", mock_post)
    
    expected_body = ("x" * 500) + "..."
    with pytest.raises(LLMFatalError, match=f"Fatal provider error: 400 - {expected_body}"):
        adapter.generate_structured("sys", "user", DummyResponse)

def test_openai_adapter_prompt_limit():
    adapter = OpenAICompatibleAdapter(api_key="test")
    
    with pytest.raises(LLMFatalError, match="Prompt length exceeds safety threshold"):
        adapter.generate_structured("sys" * 10000, "user" * 10000, DummyResponse)


def test_openai_adapter_success(monkeypatch):
    adapter = OpenAICompatibleAdapter(api_key="test")

    def mock_post(*args, **kwargs):
        return MockResponse(200, json_data={
            "choices": [{"message": {"content": '{"value": 42}'}}]
        })

    monkeypatch.setattr(httpx.Client, "post", mock_post)

    res = adapter.generate_structured("sys", "user", DummyResponse)
    assert res.value == 42


def test_openai_adapter_sends_max_completion_tokens_not_max_tokens(monkeypatch):
    """
    Task 17: Groq's OpenAI-compatible endpoint (and specifically the
    openai/gpt-oss-* reasoning models) expects max_completion_tokens, not the
    legacy max_tokens field. When a caller supplies max_tokens to our own
    provider-abstraction method, the adapter must translate it to
    max_completion_tokens in the actual outgoing payload.
    """
    adapter = OpenAICompatibleAdapter(api_key="test")
    captured_payload = {}

    def mock_post(self, url, headers=None, json=None):
        captured_payload.update(json)
        return MockResponse(200, json_data={
            "choices": [{"message": {"content": '{"value": 42}'}}]
        })

    monkeypatch.setattr(httpx.Client, "post", mock_post)

    adapter.generate_structured("sys", "user", DummyResponse, max_tokens=8192)

    assert captured_payload.get("max_completion_tokens") == 8192
    assert "max_tokens" not in captured_payload


def test_openai_adapter_omits_token_budget_when_not_supplied(monkeypatch):
    """When no max_tokens is passed (e.g. the untouched answer-evaluation
    caller), neither max_tokens nor max_completion_tokens should appear --
    behavior for callers that don't opt in must stay exactly as before."""
    adapter = OpenAICompatibleAdapter(api_key="test")
    captured_payload = {}

    def mock_post(self, url, headers=None, json=None):
        captured_payload.update(json)
        return MockResponse(200, json_data={
            "choices": [{"message": {"content": '{"value": 42}'}}]
        })

    monkeypatch.setattr(httpx.Client, "post", mock_post)

    adapter.generate_structured("sys", "user", DummyResponse)

    assert "max_completion_tokens" not in captured_payload
    assert "max_tokens" not in captured_payload


def test_openai_adapter_classifies_groq_json_validate_failed_as_fatal(monkeypatch):
    """
    Regression for the real observed Task 16 failure: Groq returns HTTP 400
    with code=json_validate_failed and an empty failed_generation when the
    reasoning model exhausts its token budget without emitting a final
    answer. This must still be classified as a fatal (non-retried-by-adapter)
    error, exactly like any other 400 -- the adapter's error classification
    itself does not change, only the token budget supplied to prevent the
    condition in the first place.
    """
    adapter = OpenAICompatibleAdapter(api_key="test")

    groq_error_body = (
        '{"error":{"message":"'
        "'None' is not a valid value under the schema. "
        'json_validate_failed","code":"json_validate_failed",'
        '"request_id":"req_123"},"failed_generation":""}'
    )

    def mock_post(*args, **kwargs):
        return MockResponse(400, text=groq_error_body)

    monkeypatch.setattr(httpx.Client, "post", mock_post)

    with pytest.raises(LLMFatalError, match="json_validate_failed"):
        adapter.generate_structured("sys", "user", DummyResponse, max_tokens=8192)
