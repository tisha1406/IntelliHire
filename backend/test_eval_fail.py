import asyncio
import os
from app.ai_interview.answer_engine.llm_answer_evaluator import LLMAnswerEvaluator
from app.ai_interview.answer_engine.schemas import EvaluationRequest
from app.ai_interview.core.enums import DifficultyLevel, QuestionType
from app.ai_interview.llm_infrastructure.adapters.openai_adapter import OpenAICompatibleAdapter

async def main():
    try:
        provider = OpenAICompatibleAdapter()
        evaluator = LLMAnswerEvaluator(provider)
        request = EvaluationRequest(
            session_id="test",
            question_record_id="test",
            topic_id="test",
            topic_name="Introduction and Background",
            question_text="Walk me through a recent project you worked on.",
            question_type=QuestionType.INITIAL,
            difficulty=DifficultyLevel.MEDIUM,
            candidate_answer="Recently I worked on an AI-based interview platform. One challenge was integrating the interview engine with the frontend and making the session recover correctly after connection failures. I solved it by separating the runtime state and WebSocket reconnection logic."
        )
        res = evaluator.evaluate(request)
        from app.ai_interview.answer_engine.evaluation_validator import EvaluationValidator
        from app.ai_interview.answer_engine.evaluation_normalizer import EvaluationNormalizer
        from app.ai_interview.answer_engine.coverage_assessor import CoverageAssessor
        from app.ai_interview.answer_engine.evaluation_applicator import EvaluationApplicator
        from app.ai_interview.schemas.session import InterviewSessionSchema, TopicProgress
        
        EvaluationValidator.validate(res)
        result = EvaluationNormalizer.normalize(res, request)
        print("Normalized result:", result)
        
        session = InterviewSessionSchema(
            session_id="test",
            candidate_id="c1",
            campaign_id="c1",
            mode_id="practice",
            blueprint={"topics": [{"topic_id": "test", "topic_name": "Test", "question_budget": 3, "min_questions": 1}]},
            topic_progress=[TopicProgress(topic_id="test", questions_asked=1, structurally_attempted=False, qualitatively_covered=False)]
        )
        topic_progress = session.topic_progress[0]
        assessment = CoverageAssessor.assess(topic_progress.evaluation_aggregate, result, topic_progress, 3)
        EvaluationApplicator.apply(session, topic_progress, result, assessment)
        print("Success! Evaluation applied.")
    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
