import pytest
from pydantic import BaseModel
from app.ai_interview.llm_infrastructure.parsers import StructuredOutputParser
from app.ai_interview.llm_infrastructure.exceptions import LLMValidationError

class DummyModel(BaseModel):
    score: int
    feedback: str

def test_parser_valid_json():
    raw = '{"score": 8, "feedback": "good"}'
    res = StructuredOutputParser.parse_and_validate(raw, DummyModel)
    assert res.score == 8
    assert res.feedback == "good"

def test_parser_markdown_fence():
    raw = "Here is the json:\n```json\n{\"score\": 9, \"feedback\": \"great\"}\n```\nHope it helps!"
    res = StructuredOutputParser.parse_and_validate(raw, DummyModel)
    assert res.score == 9

def test_parser_trailing_comma_recovery():
    raw = '{"score": 5, "feedback": "ok",}'
    res = StructuredOutputParser.parse_and_validate(raw, DummyModel)
    assert res.score == 5

def test_parser_missing_fields_rejected():
    raw = '{"score": 7}'
    with pytest.raises(LLMValidationError, match="validation failed"):
        StructuredOutputParser.parse_and_validate(raw, DummyModel)

def test_parser_malformed_json_rejected():
    raw = '{"score": 7, "feedback": "broken'
    with pytest.raises(LLMValidationError, match="decode JSON"):
        StructuredOutputParser.parse_and_validate(raw, DummyModel)

def test_parser_invalid_schema_type():
    raw = '{"score": "not_an_int", "feedback": "bad type"}'
    with pytest.raises(LLMValidationError, match="validation failed"):
        StructuredOutputParser.parse_and_validate(raw, DummyModel)

def test_parser_excessive_response_size():
    raw = '{"score": 8, "feedback": "' + ("a" * 60000) + '"}'
    with pytest.raises(LLMValidationError, match="too large to parse"):
        StructuredOutputParser.parse_and_validate(raw, DummyModel)
