import logging
from app.ai_interview.question_engine.question_generator import QuestionGenerator
from app.ai_interview.question_engine.schemas import QuestionGenerationRequest, GeneratedQuestion
from app.ai_interview.question_engine.exceptions import QuestionGenerationError
from app.ai_interview.llm_infrastructure.interfaces import LLMProvider
from app.ai_interview.llm_infrastructure.prompts import PromptCompiler
from app.ai_interview.llm_infrastructure.resilience import ResiliencePolicy

logger = logging.getLogger(__name__)

# Task 16 audit finding: generation requests previously had no explicit token
# budget, so the configured reasoning model (openai/gpt-oss-20b) could consume
# its entire default allocation on internal reasoning before emitting any
# visible JSON, producing Groq's "json_validate_failed" with an empty
# failed_generation. 8192 matches Groq's own published example budget for this
# model (well under its 65536 max) -- generous enough for substantial
# reasoning plus a short GeneratedQuestion JSON object, without being
# arbitrarily large.
QUESTION_GENERATION_MAX_TOKENS = 8192

class LLMQuestionGenerator(QuestionGenerator):
    """
    Concrete QuestionGenerator that leverages the generic LLMProvider abstraction.
    Does NOT depend on a specific LLM like OpenAI or Gemini.
    """
    
    def __init__(self, provider: LLMProvider):
        self.provider = provider
        
    def generate(
        self,
        request: QuestionGenerationRequest,
        attempt_number: int = 1,
    ) -> GeneratedQuestion:
        
        try:
            if request.strategy_id and request.interview_type:
                from app.ai_interview.question_engine.prompts import PromptResolver
                sys_compiled, user_compiled = PromptResolver.resolve(request)
            else:
                from app.ai_interview.question_engine.prompts.question_generation import get_system_prompt, build_user_message
                sys_compiled = get_system_prompt()
                user_compiled = build_user_message(request)
            
            generated = self.provider.generate_structured(
                system_prompt=sys_compiled,
                user_prompt=user_compiled,
                response_model=GeneratedQuestion,
                temperature=0.7 + (attempt_number * 0.1),
                max_tokens=QUESTION_GENERATION_MAX_TOKENS,
            )
            
            # Topic, question type and difficulty are deterministic backend
            # decisions; the model only writes the question text. The library
            # prompt (PromptResolver) never exposes the internal topic_id or
            # the selected question type, so the model can only guess them
            # (observed with the real provider: topic_id echoed as the topic
            # name, question_type "clarification" for a follow-up whose
            # selected type is "initial"). QuestionValidator requires exact
            # matches, so pin all three to the request, exactly as
            # FakeQuestionGenerator already returns them.
            return generated.model_copy(update={
                "topic_id": request.topic_id,
                "question_type": request.selected_question_type,
                "difficulty": request.difficulty,
            })

        except Exception as e:
            logger.error(f"LLMQuestionGenerator failed on attempt {attempt_number}: {e}")
            raise QuestionGenerationError(f"LLM Provider failure: {e}") from e
