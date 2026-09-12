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
    
    with pytest.raises(LLMTransientError, match="Transient provider error: 500"):
        adapter.generate_structured("sys", "user", DummyResponse)


def test_openai_adapter_fatal_error(monkeypatch):
    adapter = OpenAICompatibleAdapter(api_key="test")
    
    def mock_post(*args, **kwargs):
        return MockResponse(401, text="Unauthorized")
        
    monkeypatch.setattr(httpx.Client, "post", mock_post)
    
    with pytest.raises(LLMFatalError, match="Fatal provider error: 401"):
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
