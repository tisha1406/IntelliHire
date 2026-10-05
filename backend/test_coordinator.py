import asyncio
from app.ai_interview.orchestration.interview_turn_coordinator import InterviewTurnCoordinator
from app.ai_interview.question_engine.question_engine import QuestionEngine
from app.ai_interview.question_engine.question_generator import QuestionGenerator
from app.ai_interview.question_engine.llm_question_generator import LLMQuestionGenerator
from app.ai_interview.answer_engine.answer_engine import AnswerEngine
from app.ai_interview.answer_engine.llm_answer_evaluator import LLMAnswerEvaluator
from app.ai_interview.llm_infrastructure.adapters.openai_adapter import OpenAICompatibleAdapter
from app.ai_interview.schemas.session import InterviewSessionSchema, TopicProgress, QuestionRecord
from app.ai_interview.schemas.interview_mode import InterviewModeDefinition, InterviewModeSettings, InterviewModeStatus
from app.ai_interview.resume_processing.schemas import CandidateInterviewContext, StructuredResume
from app.ai_interview.answer_engine.schemas import AnswerSubmission
from app.ai_interview.core.enums import InterviewState, QuestionType, DifficultyLevel
from datetime import datetime, timezone

async def main():
    try:
        provider = OpenAICompatibleAdapter()
        q_gen = LLMQuestionGenerator(provider)
        a_eval = LLMAnswerEvaluator(provider)
        q_engine = QuestionEngine(q_gen)
        a_engine = AnswerEngine(a_eval)
        coordinator = InterviewTurnCoordinator(q_engine, a_engine)

        mode = InterviewModeDefinition(
            mode_id="practice",
            name="Practice Mode",
            description="Practice",
            version=1,
            status=InterviewModeStatus.PUBLISHED,
            settings=InterviewModeSettings(
                allowed_question_types=["initial", "follow_up"],
                question_style="conversational",
            ),
            created_at=datetime.now(timezone.utc)
        )

        session = InterviewSessionSchema(
            session_id="s1",
            candidate_id="c1",
            campaign_id="c1",
            company_id="c1",
            created_at=datetime.now(timezone.utc),
            mode_id="practice",
            mode_version=1,
            state=InterviewState.IN_PROGRESS,
            blueprint={
                "topics": [
                    {"topic_id": "intro", "topic_name": "Intro", "question_budget": 1, "min_questions": 1, "priority": 1, "source": "practice", "mandatory": True},
                    {"topic_id": "recent_work", "topic_name": "Recent Work", "question_budget": 1, "min_questions": 1, "priority": 2, "source": "practice", "mandatory": True},
                    {"topic_id": "proudest", "topic_name": "Proudest Project", "question_budget": 1, "min_questions": 1, "priority": 3, "source": "practice", "mandatory": True},
                ],
                "blueprint_version": "1",
                "total_question_budget": 3,
                "min_questions": 3,
                "max_questions": 3,
                "emergency_max_questions": 5
            },
            topic_progress=[
                TopicProgress(topic_id="intro", questions_asked=1, structurally_attempted=True, qualitatively_covered=False, state="failed_abandoned"),
                TopicProgress(topic_id="recent_work", questions_asked=1, structurally_attempted=False, qualitatively_covered=False, state="in_progress"),
                TopicProgress(topic_id="proudest", questions_asked=0, state="not_started")
            ],
            current_topic_id="recent_work",
            questions_asked_total=2,
            question_history=[
                QuestionRecord(
                    record_id="q1",
                    session_id="s1",
                    turn_number=1,
                    topic_id="intro",
                    question_text="Walk me through a recent project.",
                    question_type=QuestionType.INITIAL,
                    difficulty=DifficultyLevel.MEDIUM,
                    status="evaluated"
                ),
                QuestionRecord(
                    record_id="q2",
                    session_id="s1",
                    turn_number=2,
                    topic_id="recent_work",
                    question_text="Tell me about a specific challenge you faced.",
                    question_type=QuestionType.INITIAL,
                    difficulty=DifficultyLevel.MEDIUM,
                    status="evaluation_pending"
                )
            ]
        )

        candidate_context = CandidateInterviewContext(
            candidate_id="c1",
            structured_resume=StructuredResume(skills=[], projects=[], experience=[]),
            extraction_metadata={
                "source_type": "text",
                "extractor_name": "test",
                "extractor_version": "1.0",
                "character_count": 0,
                "detected_sections": [],
                "warning_count": 0,
                "processing_duration_ms": 0
            },
            quality_status="USABLE"
        )

        submission = AnswerSubmission(
            session_id="s1",
            question_record_id="q2",
            answer_text="I learned a lot about resilience and system architecture."
        )

        result = coordinator.advance_interview(session, candidate_context, mode, submission)
        print("Success!", result)
    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
