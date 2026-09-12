import logging
from app.ai_interview.question_engine.question_generator import QuestionGenerator
from app.ai_interview.question_engine.schemas import QuestionGenerationRequest, GeneratedQuestion
from app.ai_interview.question_engine.exceptions import QuestionGenerationError
from app.ai_interview.llm_infrastructure.interfaces import LLMProvider
from app.ai_interview.llm_infrastructure.prompts import PromptCompiler
from app.ai_interview.llm_infrastructure.resilience import ResiliencePolicy

logger = logging.getLogger(__name__)

class LLMQuestionGenerator(QuestionGenerator):
    """
    Concrete QuestionGenerator that leverages the generic LLMProvider abstraction.
    Does NOT depend on a specific LLM like OpenAI or Gemini.
    """
    
    def __init__(self, provider: LLMProvider):
        self.provider = provider
        
        self.system_prompt = (
            "You are an expert technical interviewer. Your task is to generate EXACTLY ONE interview question.\n"
            "You must follow the constraints provided exactly.\n"
            "Difficulty: {difficulty}\n"
            "Question Type: {question_type}\n"
            "Topic: {topic_name}\n"
            "Do NOT repeat any of these previous questions: {previous_questions}\n"
        )
        
        self.user_prompt = (
            "Generate a {question_type} question for the topic '{topic_name}' "
            "at {difficulty} difficulty.\n"
            "Relevant context:\n"
            "Skills: {skills}\n"
            "Experience: {experience}\n"
        )

    def generate(
        self,
        request: QuestionGenerationRequest,
        attempt_number: int = 1,
    ) -> GeneratedQuestion:
        
        try:
            sys_compiled = PromptCompiler.compile(
                self.system_prompt,
                difficulty=request.difficulty.value,
                question_type=request.selected_question_type.value,
                topic_name=request.topic_name,
                previous_questions=" | ".join(request.previous_questions) if request.previous_questions else "None"
            )
            
            user_compiled = PromptCompiler.compile(
                self.user_prompt,
                difficulty=request.difficulty.value,
                question_type=request.selected_question_type.value,
                topic_name=request.topic_name,
                skills=", ".join(request.relevant_skills),
                experience=", ".join(request.relevant_experience)
            )
            
            # Using ResiliencePolicy directly via execute_with_retry inside QuestionEngine or here?
            # Actually, QuestionEngine handles generation retries via MAX_GENERATION_ATTEMPTS natively.
            # So we don't need a double retry loop here.
            
            generated = self.provider.generate_structured(
                system_prompt=sys_compiled,
                user_prompt=user_compiled,
                response_model=GeneratedQuestion,
                temperature=0.7 + (attempt_number * 0.1)  # slightly increase temp on retry
            )
            
            return generated
            
        except Exception as e:
            logger.error(f"LLMQuestionGenerator failed on attempt {attempt_number}: {e}")
            raise QuestionGenerationError(f"LLM Provider failure: {e}") from e
