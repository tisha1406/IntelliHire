import pytest
from app.ai_interview.core.enums import DifficultyLevel, QuestionType
from app.ai_interview.question_engine.schemas import QuestionGenerationRequest, GeneratedQuestion
from app.ai_interview.question_engine.llm_question_generator import LLMQuestionGenerator

class MockSuccessProvider:
    def generate_structured(self, system_prompt, user_prompt, response_model, **kwargs):
        # We can assert that prompts contain no HTTP/provider specific structures
        return GeneratedQuestion(
            question_text="What is Python?",
            question_type=QuestionType.INITIAL,
            topic_id="t1",
            difficulty=DifficultyLevel.EASY,
            rationale="mock rationale"
        )
        
    def generate_text(self, *args, **kwargs):
        return "mock text"

def test_llm_question_generator_success_path():
    provider = MockSuccessProvider()
    generator = LLMQuestionGenerator(provider=provider)
    
    req = QuestionGenerationRequest(
        session_id="s1",
        turn_number=1,
        topic_id="t1",
        topic_name="Python",
        difficulty=DifficultyLevel.EASY,
        allowed_question_types=[QuestionType.INITIAL],
        selected_question_type=QuestionType.INITIAL,
        question_number=1,
        max_questions_for_topic=3
    )
    
    res = generator.generate(req)
    assert res.question_text == "What is Python?"
    assert res.topic_id == "t1"
