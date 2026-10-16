import logging
from app.ai_interview.answer_engine.answer_evaluator import AnswerEvaluator
from app.ai_interview.answer_engine.schemas import EvaluationRequest, RawEvaluation
from app.ai_interview.answer_engine.exceptions import EvaluationValidationError
from app.ai_interview.llm_infrastructure.interfaces import LLMProvider
from app.ai_interview.llm_infrastructure.prompts import PromptCompiler
from app.ai_interview.llm_infrastructure.resilience import ResiliencePolicy

logger = logging.getLogger(__name__)

# Same Groq account/quota and reasoning model as question generation (see
# llm_question_generator.py's QUESTION_GENERATION_MAX_TOKENS comment for the
# live A/B test that showed a too-small budget causes empty-output failures
# on longer/more complex prompts -- a smaller number does NOT meaningfully
# help the account's actual tokens-per-minute headroom, which live checks
# showed was not the dominant constraint). Kept generous for the same
# reason, comfortably under the model's 65536 max.
EVALUATION_MAX_TOKENS = 8192

# Evaluation calls share the same account-level rate limit as question
# generation and can hit the same HTTP 429 rate_limit_exceeded without any
# retry delay previously existing here -- AnswerEngine's own outer retry loop
# (MAX_EVALUATION_ATTEMPTS) retried immediately, hitting the same active
# rate-limit window. Same fix as question generation: real backoff via the
# existing ResiliencePolicy before AnswerEngine's own retry logic is involved.
_EVALUATION_RESILIENCE_MAX_ATTEMPTS = 2
_EVALUATION_RESILIENCE_BASE_DELAY_SECONDS = 2.0
_EVALUATION_RESILIENCE_MAX_OPERATION_SECONDS = 20.0

class LLMAnswerEvaluator(AnswerEvaluator):
    """
    Concrete AnswerEvaluator using generic LLMProvider.
    """
    
    def __init__(self, provider: LLMProvider):
        self.provider = provider
        
        self.system_prompt = (
            "You are an expert technical interviewer evaluating a candidate's answer.\n"
            "Score the answer strictly out of 1.0 according to the provided rubrics.\n"
            "Topic: {topic_name}\n"
            "Difficulty: {difficulty}\n"
        )
        
        self.user_prompt = (
            "Question asked: {question_text}\n"
            "Candidate Answer: {answer_text}\n"
            "Please evaluate this answer."
        )

    def evaluate(self, request: EvaluationRequest) -> RawEvaluation:
        try:
            sys_compiled = PromptCompiler.compile(
                self.system_prompt,
                topic_name=request.topic_name,
                difficulty=request.difficulty.value
            )
            
            user_compiled = PromptCompiler.compile(
                self.user_prompt,
                question_text=request.question_text,
                answer_text=request.candidate_answer
            )
            
            # Use provider to parse and validate into RawEvaluation
            raw_evaluation = ResiliencePolicy.execute_with_retry(
                self.provider.generate_structured,
                max_attempts=_EVALUATION_RESILIENCE_MAX_ATTEMPTS,
                base_delay_seconds=_EVALUATION_RESILIENCE_BASE_DELAY_SECONDS,
                max_operation_time_seconds=_EVALUATION_RESILIENCE_MAX_OPERATION_SECONDS,
                system_prompt=sys_compiled,
                user_prompt=user_compiled,
                response_model=RawEvaluation,
                temperature=0.3, # Low temp for deterministic evaluation
                max_tokens=EVALUATION_MAX_TOKENS,
            )
            
            return raw_evaluation
            
        except Exception as e:
            logger.error(f"LLMAnswerEvaluator failed: {e}")
            # The Engine retry loop expects EvaluationValidationError or RuntimeError
            raise EvaluationValidationError(f"LLM Provider failure: {e}") from e
