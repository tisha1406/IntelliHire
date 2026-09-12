import logging
from app.ai_interview.answer_engine.answer_evaluator import AnswerEvaluator
from app.ai_interview.answer_engine.schemas import EvaluationRequest, RawEvaluation
from app.ai_interview.answer_engine.exceptions import EvaluationValidationError
from app.ai_interview.llm_infrastructure.interfaces import LLMProvider
from app.ai_interview.llm_infrastructure.prompts import PromptCompiler

logger = logging.getLogger(__name__)

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
            raw_evaluation = self.provider.generate_structured(
                system_prompt=sys_compiled,
                user_prompt=user_compiled,
                response_model=RawEvaluation,
                temperature=0.3 # Low temp for deterministic evaluation
            )
            
            return raw_evaluation
            
        except Exception as e:
            logger.error(f"LLMAnswerEvaluator failed: {e}")
            # The Engine retry loop expects EvaluationValidationError or RuntimeError
            raise EvaluationValidationError(f"LLM Provider failure: {e}") from e
