"""
Regression: real-provider end-to-end verification (Task 7) found that, with
the PromptResolver library prompt, a real model could never produce a question
that passed QuestionValidator:

  * first question: the prompt never contains the internal topic_id, so the
    model guessed it -- it echoed the topic NAME ("Python");
  * follow-up: the validator expects selected_question_type (the topic's
    allowed_question_types[0], "initial"), which the model cannot know -- it
    answered "clarification" three times in a row, so every follow-up failed.

FakeQuestionGenerator returns the request's values by construction, which is
why no earlier test saw it. Topic, type and difficulty are deterministic
backend decisions, so LLMQuestionGenerator pins all three to the request.
"""
import app.ai_interview.schemas.session  # noqa: F401  (avoid circular import)
from app.ai_interview.core.enums import DifficultyLevel, InterviewType, QuestionCategory, QuestionType
from app.ai_interview.question_engine.llm_question_generator import LLMQuestionGenerator
from app.ai_interview.question_engine.question_validator import QuestionValidator
from app.ai_interview.question_engine.schemas import GeneratedQuestion, QuestionGenerationRequest

TOPIC_ID = "8706f2ac-a3c0-4469-ab3d-79dac8b8c8b7"
TEXT = "What are the differences between a list and a tuple in Python?"


class _ProviderGuessing:
    """Behaves like the real model did: valid JSON, backend-owned fields guessed."""
    def __init__(self, topic_id="Python", question_type=QuestionType.INITIAL, difficulty=DifficultyLevel.MEDIUM):
        self._q = GeneratedQuestion(question_text=TEXT, question_type=question_type,
                                    topic_id=topic_id, difficulty=difficulty)

    def generate_structured(self, system_prompt, user_prompt, response_model, **kwargs):
        return self._q


def _request(category=QuestionCategory.NEW, difficulty=DifficultyLevel.MEDIUM):
    return QuestionGenerationRequest(
        session_id="s1", turn_number=1, topic_id=TOPIC_ID, topic_name="Python",
        difficulty=difficulty,
        allowed_question_types=[QuestionType.INITIAL, QuestionType.FOLLOW_UP],
        selected_question_type=QuestionType.INITIAL,
        question_number=1, max_questions_for_topic=3,
        strategy_id="adaptive_depth", interview_type=InterviewType.TECHNICAL, category=category,
    )


def test_first_question_passes_validation_even_if_model_guesses_topic_id():
    request = _request()

    generated = LLMQuestionGenerator(_ProviderGuessing(topic_id="Python")).generate(request)

    assert generated.topic_id == TOPIC_ID
    QuestionValidator.validate(generated, request)  # previously: "Topic ID mismatch"


def test_followup_passes_validation_even_if_model_guesses_question_type_and_difficulty():
    # Exactly what the real provider returned for a followup_clarification turn.
    request = _request(category=QuestionCategory.FOLLOWUP_CLARIFICATION, difficulty=DifficultyLevel.EASY)
    provider = _ProviderGuessing(question_type=QuestionType.CLARIFICATION, difficulty=DifficultyLevel.HARD)

    generated = LLMQuestionGenerator(provider).generate(request)

    assert generated.question_type == QuestionType.INITIAL
    assert generated.difficulty == DifficultyLevel.EASY
    QuestionValidator.validate(generated, request)  # previously: "Question type mismatch"


def test_pinning_never_touches_the_question_text():
    generated = LLMQuestionGenerator(_ProviderGuessing()).generate(_request())

    assert generated.question_text == TEXT
