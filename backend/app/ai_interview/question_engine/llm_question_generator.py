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
# failed_generation.
#
# This was first lowered to 4096 on the theory that a smaller budget would
# ease pressure on the account's tokens-per-minute cap. Live A/B testing
# against the real account disproved that: replaying the EXACT context of a
# real production failure (a later-turn question with 6 prior questions
# already accumulated in the duplicate-avoidance context, i.e. a longer,
# more complex prompt) failed 1/6 times at 4096 tokens but 0/6 times at
# 16384 -- longer/more complex prompts need more reasoning headroom, not
# less, and real-time account-quota checks showed plenty of
# tokens-per-minute headroom even right after a real failure, so the TPM
# cap was not actually the dominant constraint for normal interview pacing.
# 16384 is comfortably under the model's 65536 max.
QUESTION_GENERATION_MAX_TOKENS = 16384

# Live testing against the real Groq account surfaced two *distinct* failure
# modes on attempt: (a) the json_validate_failed/empty-output case above, and
# (b) HTTP 429 rate_limit_exceeded -- the configured account has an 8000
# tokens-per-minute cap, comfortably exceeded by a real interview's generation
# + evaluation calls. 429 is correctly classified as LLMTransientError by the
# adapter, but nothing previously retried it with any delay: QuestionEngine's
# outer retry loop (3 attempts, varying temperature) calls generate() again
# immediately, which hits the exact same still-active rate-limit window and
# exhausts all attempts in well under a second. Wrapping just the provider
# call in the existing (previously unused) ResiliencePolicy gives transient
# errors real backoff -- enough for Groq's own "try again in Ns" window to
# pass -- before QuestionEngine's own retry/temperature logic is ever
# involved. LLMFatalError (e.g. json_validate_failed) is NOT retried here;
# ResiliencePolicy re-raises it immediately, exactly as QuestionEngine's own
# retry loop already expects.
_GENERATION_RESILIENCE_MAX_ATTEMPTS = 2
_GENERATION_RESILIENCE_BASE_DELAY_SECONDS = 2.0
_GENERATION_RESILIENCE_MAX_OPERATION_SECONDS = 20.0

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
            
            generated = ResiliencePolicy.execute_with_retry(
                self.provider.generate_structured,
                max_attempts=_GENERATION_RESILIENCE_MAX_ATTEMPTS,
                base_delay_seconds=_GENERATION_RESILIENCE_BASE_DELAY_SECONDS,
                max_operation_time_seconds=_GENERATION_RESILIENCE_MAX_OPERATION_SECONDS,
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
