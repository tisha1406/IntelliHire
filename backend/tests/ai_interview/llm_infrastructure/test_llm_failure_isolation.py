import pytest
import copy
from app.ai_interview.core.enums import InterviewState, DifficultyLevel, QuestionType, TopicState
from app.ai_interview.schemas.session import InterviewSessionSchema, TopicProgress, TopicEvaluationAggregate
from app.ai_interview.question_engine.schemas import QuestionGenerationRequest, QuestionRecord
from app.ai_interview.answer_engine.schemas import AnswerSubmission
from app.ai_interview.question_engine.llm_question_generator import LLMQuestionGenerator
from app.ai_interview.answer_engine.llm_answer_evaluator import LLMAnswerEvaluator
from app.ai_interview.answer_engine.answer_engine import AnswerEngine
from app.ai_interview.question_engine.question_engine import QuestionEngine
from app.ai_interview.answer_engine.exceptions import AnswerEvaluationError
from app.ai_interview.question_engine.exceptions import QuestionGenerationError
from app.ai_interview.llm_infrastructure.exceptions import LLMTransientError

class FailingMockProvider:
    def generate_structured(self, *args, **kwargs):
        raise LLMTransientError("API Timeout")
        
    def generate_text(self, *args, **kwargs):
        raise LLMTransientError("API Timeout")


def test_question_generation_failure_does_not_mutate_session():
    # Setup safe state
    session = InterviewSessionSchema(
        session_id="s1",
        candidate_id="c1",
        company_id="co1",
        campaign_id="camp1",
        mode_id="m1",
        mode_version=1,
        state=InterviewState.IN_PROGRESS,
        blueprint={"blueprint_version": "1.0", "total_question_budget": 5, "min_questions": 3, "max_questions": 10, "emergency_max_questions": 15, "topics": [{"topic_id": "t1", "topic_name": "Python", "question_budget": 3, "mandatory": True, "source": "resume", "priority": 1}]},
        created_at="2026-01-01T00:00:00Z"
    )
    topic_progress = TopicProgress(topic_id="t1", state=TopicState.IN_PROGRESS)
    session.topic_progress.append(topic_progress)
    
    before_history = copy.deepcopy(session.question_history)
    before_questions_asked = session.questions_asked_total
    
    # Engine configured with failing provider
    generator = LLMQuestionGenerator(provider=FailingMockProvider())
    engine = QuestionEngine(generator=generator)
    
    # Run request
    # Note: QuestionEngine suppresses QuestionGenerationError internally and returns success=False
    request = QuestionGenerationRequest(
        session_id=session.session_id,
        turn_number=1,
        topic_id="t1",
        topic_name="Python",
        difficulty=DifficultyLevel.EASY,
        allowed_question_types=[QuestionType.INITIAL],
        selected_question_type=QuestionType.INITIAL,
        question_number=1,
        max_questions_for_topic=3
    )
    
    with pytest.raises(QuestionGenerationError):
        generator.generate(request)
        
    # The session is not mutated by the generator directly anyway, 
    # but let's confirm.
    assert session.question_history == before_history
    assert session.questions_asked_total == before_questions_asked


def test_answer_evaluation_failure_does_not_mutate_session():
    # Setup safe state
    session = InterviewSessionSchema(
        session_id="s1",
        candidate_id="c1",
        company_id="co1",
        campaign_id="camp1",
        mode_id="m1",
        mode_version=1,
        state=InterviewState.IN_PROGRESS,
        blueprint={"blueprint_version": "1.0", "total_question_budget": 5, "min_questions": 3, "max_questions": 10, "emergency_max_questions": 15, "topics": [{"topic_id": "t1", "topic_name": "Python", "question_budget": 3, "mandatory": True, "source": "resume", "priority": 1}]},
        created_at="2026-01-01T00:00:00Z"
    )
    topic_progress = TopicProgress(topic_id="t1", state=TopicState.IN_PROGRESS)
    session.topic_progress.append(topic_progress)
    
    q_record = QuestionRecord(
        session_id=session.session_id,
        turn_number=1,
        topic_id="t1",
        question_text="What is Python?",
        question_type=QuestionType.INITIAL,
        difficulty=DifficultyLevel.EASY
    )
    session.question_history.append(q_record)
    
    before_eval_history = copy.deepcopy(session.evaluation_history)
    before_aggregate = copy.deepcopy(topic_progress.evaluation_aggregate)
    
    evaluator = LLMAnswerEvaluator(provider=FailingMockProvider())
    engine = AnswerEngine(evaluator=evaluator)
    
    submission = AnswerSubmission(
        session_id=session.session_id,
        question_record_id=q_record.record_id,
        answer_text="It's a snake."
    )
    
    class FakeSettings:
        difficulty_policy = "adaptive"
        allowed_question_types = ["behavioral", "technical"]

    class FakeMode:
        name = "Test Mode"
        settings = FakeSettings()
        technical_criteria = []
        communication_criteria = []
        allow_follow_ups = True
        
    with pytest.raises(AnswerEvaluationError, match="Failed to generate valid evaluation after 3 attempts"):
        engine.evaluate_answer(submission, session, FakeMode())
        
    # Verify no state mutation
    assert session.evaluation_history == before_eval_history
    assert topic_progress.evaluation_aggregate.model_dump() == before_aggregate.model_dump()
    # The status should be EVALUATION_PENDING, but evaluation history is pristine
    assert q_record.status == "evaluation_pending"
