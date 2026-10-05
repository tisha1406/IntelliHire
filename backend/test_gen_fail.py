import asyncio
import app.ai_interview.schemas.session
from app.ai_interview.question_engine.schemas import QuestionGenerationRequest
from app.ai_interview.question_engine.llm_question_generator import LLMQuestionGenerator
from app.ai_interview.core.enums import DifficultyLevel, QuestionType
from app.ai_interview.llm_infrastructure.adapters.openai_adapter import OpenAICompatibleAdapter

async def main():
    try:
        provider = OpenAICompatibleAdapter()
        generator = LLMQuestionGenerator(provider)
        request = QuestionGenerationRequest(
            session_id="test",
            turn_number=3,
            topic_id="proudest_project",
            topic_name="Proudest Project or Contribution",
            mode_id="practice",
            question_style="conversational",
            difficulty=DifficultyLevel.MEDIUM,
            allowed_question_types=[QuestionType.INITIAL],
            selected_question_type=QuestionType.INITIAL,
            relevant_skills=[],
            relevant_projects=[],
            relevant_experience=[],
            relevant_job_requirements=[],
            previous_questions=["Walk me through a recent project you worked on.", "Can you describe a recent project where you had to integrate a new technology into an existing system?"],
            question_number=1,
            max_questions_for_topic=1
        )
        res = generator.generate(request)
        print("Success:", repr(res))
    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
