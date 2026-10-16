import pytest
from unittest.mock import patch, MagicMock

import app.ai_interview.schemas.session
from app.ai_interview.llm_infrastructure.adapters.openai_adapter import OpenAICompatibleAdapter
from app.ai_interview.question_engine.llm_question_generator import LLMQuestionGenerator
from app.ai_interview.question_engine.schemas import QuestionGenerationRequest, GeneratedQuestion
from app.ai_interview.core.enums import DifficultyLevel, QuestionType
from app.ai_interview.llm_infrastructure.prompts import PromptCompiler
from app.ai_interview.question_engine.question_validator import QuestionValidator
from app.ai_interview.question_engine.exceptions import QuestionValidationError

@pytest.fixture
def mock_httpx_client():
    with patch("httpx.Client") as mock_client_class:
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.elapsed.total_seconds.return_value = 0.5
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "{}"}}]
        }
        mock_client.post.return_value = mock_response
        mock_client_class.return_value.__enter__.return_value = mock_client
        yield mock_client

def test_adapter_json_format_sent_for_groq(mock_httpx_client):
    """
    Verify an is_json=True request for the active Groq model includes the expected JSON response_format.
    """
    # Active model is openai/gpt-oss-20b or similar
    adapter = OpenAICompatibleAdapter(api_key="test", model="openai/gpt-oss-20b")
    
    # Verify is_json=True
    adapter._call_api(system_prompt="sys", user_prompt="usr", temperature=0.7, max_tokens=None, is_json=True)
    
    # Get the payload sent to httpx
    call_kwargs = mock_httpx_client.post.call_args[1]
    payload = call_kwargs["json"]
    
    assert "response_format" in payload
    assert payload["response_format"] == {"type": "json_object"}

def test_adapter_json_format_not_sent_when_false(mock_httpx_client):
    """
    Verify is_json=False does not add JSON response_format.
    """
    adapter = OpenAICompatibleAdapter(api_key="test", model="openai/gpt-oss-20b")
    
    # Verify is_json=False
    adapter._call_api(system_prompt="sys", user_prompt="usr", temperature=0.7, max_tokens=None, is_json=False)
    
    # Get the payload sent to httpx
    call_kwargs = mock_httpx_client.post.call_args[1]
    payload = call_kwargs["json"]
    
    assert "response_format" not in payload

def test_question_generator_retries_transient_error_with_backoff(monkeypatch):
    """
    Live testing against the real Groq account surfaced HTTP 429
    rate_limit_exceeded as a real, recurring failure mode (the account's low
    tokens-per-minute cap is regularly exceeded by a real interview's
    generation+evaluation calls). The adapter already classifies this as
    LLMTransientError, but LLMQuestionGenerator previously called the
    provider directly with no retry/backoff of its own, relying entirely on
    QuestionEngine's OUTER loop (which retries immediately, with zero delay,
    hitting the exact same still-active rate-limit window). This test proves
    generate() now retries a transient failure itself, with a real delay,
    before giving up -- using the existing (previously unused)
    ResiliencePolicy.
    """
    from app.ai_interview.llm_infrastructure.exceptions import LLMTransientError

    sleep_calls = []
    monkeypatch.setattr("app.ai_interview.llm_infrastructure.resilience.time.sleep", lambda s: sleep_calls.append(s))

    mock_provider = MagicMock()
    mock_provider.generate_structured.side_effect = [
        LLMTransientError("429 - rate_limit_exceeded"),
        GeneratedQuestion(
            question_text="test",
            question_type=QuestionType.INITIAL,
            topic_id="8706f2ac-a3c0-4469-ab3d-79dac8b8c8b7",
            difficulty=DifficultyLevel.MEDIUM,
        ),
    ]
    generator = LLMQuestionGenerator(provider=mock_provider)

    request = QuestionGenerationRequest(
        session_id="test_sess",
        turn_number=1,
        topic_id="8706f2ac-a3c0-4469-ab3d-79dac8b8c8b7",
        topic_name="TypeScript fluency",
        difficulty=DifficultyLevel.MEDIUM,
        allowed_question_types=[QuestionType.INITIAL],
        selected_question_type=QuestionType.INITIAL,
        relevant_skills=[],
        relevant_projects=[],
        relevant_experience=[],
        previous_questions=[],
        question_number=1,
        max_questions_for_topic=2,
    )

    result = generator.generate(request, attempt_number=1)

    assert result.question_text == "test"
    assert mock_provider.generate_structured.call_count == 2
    assert sleep_calls == [2.0]  # one backoff delay before the second internal attempt


def test_question_generator_honors_groq_retry_after_hint(monkeypatch):
    """
    A fixed short backoff can still retry into the SAME still-active
    rate-limit window Groq reported. Groq's x-ratelimit-reset-tokens response
    header tells us precisely how long until the window resets -- this test
    proves that precise hint (carried on LLMTransientError.retry_after_seconds)
    is what actually gets waited, not the generic fixed base delay.
    """
    from app.ai_interview.llm_infrastructure.exceptions import LLMTransientError

    sleep_calls = []
    monkeypatch.setattr("app.ai_interview.llm_infrastructure.resilience.time.sleep", lambda s: sleep_calls.append(s))

    mock_provider = MagicMock()
    mock_provider.generate_structured.side_effect = [
        LLMTransientError("429 - rate_limit_exceeded", retry_after_seconds=5.5),
        GeneratedQuestion(
            question_text="test",
            question_type=QuestionType.INITIAL,
            topic_id="8706f2ac-a3c0-4469-ab3d-79dac8b8c8b7",
            difficulty=DifficultyLevel.MEDIUM,
        ),
    ]
    generator = LLMQuestionGenerator(provider=mock_provider)

    request = QuestionGenerationRequest(
        session_id="test_sess",
        turn_number=1,
        topic_id="8706f2ac-a3c0-4469-ab3d-79dac8b8c8b7",
        topic_name="TypeScript fluency",
        difficulty=DifficultyLevel.MEDIUM,
        allowed_question_types=[QuestionType.INITIAL],
        selected_question_type=QuestionType.INITIAL,
        relevant_skills=[],
        relevant_projects=[],
        relevant_experience=[],
        previous_questions=[],
        question_number=1,
        max_questions_for_topic=2,
    )

    result = generator.generate(request, attempt_number=1)

    assert result.question_text == "test"
    assert sleep_calls == [5.5]  # the precise Groq hint, not the generic 2.0s default


def test_question_generator_does_not_retry_fatal_error_internally():
    """A fatal error (e.g. json_validate_failed) must NOT be retried inside
    generate() itself -- it should propagate immediately as a
    QuestionGenerationError, exactly once, so QuestionEngine's own
    outer retry loop (with its own temperature variation) is what decides
    whether to try again, not a duplicated retry layer here."""
    from app.ai_interview.llm_infrastructure.exceptions import LLMFatalError
    from app.ai_interview.question_engine.exceptions import QuestionGenerationError

    mock_provider = MagicMock()
    mock_provider.generate_structured.side_effect = LLMFatalError("400 - json_validate_failed")
    generator = LLMQuestionGenerator(provider=mock_provider)

    request = QuestionGenerationRequest(
        session_id="test_sess",
        turn_number=1,
        topic_id="8706f2ac-a3c0-4469-ab3d-79dac8b8c8b7",
        topic_name="TypeScript fluency",
        difficulty=DifficultyLevel.MEDIUM,
        allowed_question_types=[QuestionType.INITIAL],
        selected_question_type=QuestionType.INITIAL,
        relevant_skills=[],
        relevant_projects=[],
        relevant_experience=[],
        previous_questions=[],
        question_number=1,
        max_questions_for_topic=2,
    )

    with pytest.raises(QuestionGenerationError):
        generator.generate(request, attempt_number=1)

    assert mock_provider.generate_structured.call_count == 1


def test_question_generator_passes_explicit_max_tokens_to_provider():
    """
    Task 17: LLMQuestionGenerator must supply an explicit token budget on
    every generation call, so the reasoning model (openai/gpt-oss-20b) cannot
    exhaust its default allocation on internal reasoning before emitting the
    final JSON (the real observed Groq json_validate_failed/empty
    failed_generation failure from Task 16).
    """
    from app.ai_interview.question_engine.llm_question_generator import QUESTION_GENERATION_MAX_TOKENS

    mock_provider = MagicMock()
    generator = LLMQuestionGenerator(provider=mock_provider)

    request = QuestionGenerationRequest(
        session_id="test_sess",
        turn_number=1,
        topic_id="8706f2ac-a3c0-4469-ab3d-79dac8b8c8b7",
        topic_name="TypeScript fluency",
        difficulty=DifficultyLevel.MEDIUM,
        allowed_question_types=[QuestionType.INITIAL],
        selected_question_type=QuestionType.INITIAL,
        relevant_skills=[],
        relevant_projects=[],
        relevant_experience=[],
        previous_questions=[],
        question_number=1,
        max_questions_for_topic=2
    )

    mock_provider.generate_structured.return_value = GeneratedQuestion(
        question_text="test",
        question_type=QuestionType.INITIAL,
        topic_id="8706f2ac-a3c0-4469-ab3d-79dac8b8c8b7",
        difficulty=DifficultyLevel.MEDIUM
    )

    generator.generate(request, attempt_number=1)
    generator.generate(request, attempt_number=2)

    for call in mock_provider.generate_structured.call_args_list:
        assert call.kwargs["max_tokens"] == QUESTION_GENERATION_MAX_TOKENS
        assert QUESTION_GENERATION_MAX_TOKENS >= 2048  # not an arbitrarily tiny value

    # Retry temperatures remain unchanged by this fix.
    temps = [c.kwargs["temperature"] for c in mock_provider.generate_structured.call_args_list]
    assert temps == pytest.approx([0.8, 0.9])


def test_question_generator_prompt_contains_topic_id():
    """
    Verify the authoritative request.topic_id reaches the prompt and the exact UUID is used.
    """
    mock_provider = MagicMock()
    generator = LLMQuestionGenerator(provider=mock_provider)
    
    request = QuestionGenerationRequest(
        session_id="test_sess",
        turn_number=1,
        topic_id="8706f2ac-a3c0-4469-ab3d-79dac8b8c8b7",
        topic_name="TypeScript fluency",
        difficulty=DifficultyLevel.MEDIUM,
        allowed_question_types=[QuestionType.INITIAL],
        selected_question_type=QuestionType.INITIAL,
        relevant_skills=[],
        relevant_projects=[],
        relevant_experience=[],
        previous_questions=[],
        question_number=1,
        max_questions_for_topic=2
    )
    
    with patch("app.ai_interview.llm_infrastructure.prompts.PromptCompiler.compile", wraps=PromptCompiler.compile) as mock_compile:
        # We don't care about the provider generation succeeding, just the prompt compilation
        mock_provider.generate_structured.return_value = GeneratedQuestion(
            question_text="test",
            question_type=QuestionType.INITIAL,
            topic_id="8706f2ac-a3c0-4469-ab3d-79dac8b8c8b7",
            difficulty=DifficultyLevel.MEDIUM
        )
        
        generator.generate(request)
        
        # Check the call to generate_structured
        generate_call = mock_provider.generate_structured.call_args
        user_prompt = generate_call.kwargs["user_prompt"]
        
        # Verify the user prompt contains the exact UUID
        assert "8706f2ac-a3c0-4469-ab3d-79dac8b8c8b7" in user_prompt

def test_validation_passes_with_correct_topic_id():
    """
    Verify a generated question with the exact requested topic_id passes the relevant validation path.
    """
    request = QuestionGenerationRequest(
        session_id="test_sess",
        turn_number=1,
        topic_id="8706f2ac-a3c0-4469-ab3d-79dac8b8c8b7",
        topic_name="TypeScript fluency",
        difficulty=DifficultyLevel.MEDIUM,
        allowed_question_types=[QuestionType.INITIAL],
        selected_question_type=QuestionType.INITIAL,
        relevant_skills=[],
        relevant_projects=[],
        relevant_experience=[],
        previous_questions=[],
        question_number=1,
        max_questions_for_topic=2
    )
    
    # This should pass without raising QuestionValidationError
    valid_question = GeneratedQuestion(
        question_text="Can you explain utility types in TypeScript?",
        question_type=QuestionType.INITIAL,
        topic_id="8706f2ac-a3c0-4469-ab3d-79dac8b8c8b7",
        difficulty=DifficultyLevel.MEDIUM
    )
    
    # If this raises, the test fails
    QuestionValidator.validate(valid_question, request)

def test_validation_fails_with_wrong_topic_id():
    """
    Verify validation fails if topic_id does not match exactly.
    """
    request = QuestionGenerationRequest(
        session_id="test_sess",
        turn_number=1,
        topic_id="8706f2ac-a3c0-4469-ab3d-79dac8b8c8b7",
        topic_name="TypeScript fluency",
        difficulty=DifficultyLevel.MEDIUM,
        allowed_question_types=[QuestionType.INITIAL],
        selected_question_type=QuestionType.INITIAL,
        relevant_skills=[],
        relevant_projects=[],
        relevant_experience=[],
        previous_questions=[],
        question_number=1,
        max_questions_for_topic=2
    )
    
    invalid_question = GeneratedQuestion(
        question_text="Can you explain utility types in TypeScript?",
        question_type=QuestionType.INITIAL,
        topic_id="typescript_fluency", # Wrong topic_id
        difficulty=DifficultyLevel.MEDIUM
    )
    
    with pytest.raises(QuestionValidationError) as exc:
        QuestionValidator.validate(invalid_question, request)
    
    assert "Topic ID mismatch" in str(exc.value)
