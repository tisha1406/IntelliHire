import pytest
from app.ai_interview.core.enums import InterviewState, DifficultyLevel, QuestionType, TopicState
from app.ai_interview.schemas.session import InterviewSessionSchema, TopicProgress
from app.ai_interview.question_engine.schemas import QuestionRecord
from app.ai_interview.answer_engine.schemas import AnswerSubmission, EvaluationResult, RawEvaluation, CoverageSignal, FollowUpSignal
from app.ai_interview.answer_engine.answer_engine import AnswerEngine
from app.ai_interview.answer_engine.llm_answer_evaluator import LLMAnswerEvaluator
from app.ai_interview.llm_infrastructure.exceptions import LLMTransientError

class RecoveringMockProvider:
    def __init__(self):
        self.calls = 0
        
    def generate_structured(self, system_prompt, user_prompt, response_model, **kwargs):
        self.calls += 1
        if self.calls == 1:
            # Fail the first time
            raise LLMTransientError("API down")
        
        # Succeed the second time
        return RawEvaluation(
            relevance_score=0.8,
            correctness_score=0.8,
            depth_score=0.8,
            clarity_score=0.8,
            overall_score=0.8,
            strengths=["Good"],
            weaknesses=[],
            missing_concepts=[],
            evidence_summary="Solid.",
            follow_up_signal=FollowUpSignal.NONE,
            qualitative_coverage_signal=CoverageSignal.PARTIALLY_COVERED
        )
        
    def generate_text(self, *args, **kwargs):
        return ""

def test_failure_recovery_allows_retry_from_pending(monkeypatch):
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
        difficulty=DifficultyLevel.EASY,
        status="answer_received"
    )
    session.question_history.append(q_record)
    
    provider = RecoveringMockProvider()
    evaluator = LLMAnswerEvaluator(provider=provider)
    engine = AnswerEngine(evaluator=evaluator)
    
    submission = AnswerSubmission(
        session_id=session.session_id,
        question_record_id=q_record.record_id,
        answer_text="It's a language."
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
        
    # Set max attempts to 1 for this test so we can manually simulate the retry across boundaries
    import app.ai_interview.answer_engine.answer_engine as ae_module
    monkeypatch.setattr(ae_module, "MAX_EVALUATION_ATTEMPTS", 1)
    
    # ATTEMPT 1 - Should fail due to provider
    from app.ai_interview.answer_engine.exceptions import AnswerEvaluationError
    with pytest.raises(AnswerEvaluationError):
        engine.evaluate_answer(submission, session, FakeMode())
        
    # State should be pending
    assert q_record.status == "evaluation_pending"
    assert len(session.evaluation_history) == 0
    
    # ATTEMPT 2 - We submit the same answer again
    res = engine.evaluate_answer(submission, session, FakeMode())
    
    assert res is not None
    assert q_record.status == "evaluated"
    assert len(session.evaluation_history) == 1
    
    # ATTEMPT 3 - Try again! Idempotency should block it and avoid LLM call!
    from app.ai_interview.answer_engine.exceptions import QuestionCorrelationError
    calls_before = provider.calls
    with pytest.raises(QuestionCorrelationError, match="has already been evaluated"):
        engine.evaluate_answer(submission, session, FakeMode())
        
    assert provider.calls == calls_before # Proof that duplication is caught before provider call
