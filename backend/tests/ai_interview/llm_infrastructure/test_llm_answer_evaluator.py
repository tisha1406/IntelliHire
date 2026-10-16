import pytest
from app.ai_interview.core.enums import DifficultyLevel, QuestionType
from app.ai_interview.answer_engine.enums import FollowUpSignal
from app.ai_interview.answer_engine.schemas import EvaluationRequest, RawEvaluation, CoverageSignal
from app.ai_interview.answer_engine.llm_answer_evaluator import LLMAnswerEvaluator

class MockSuccessProvider:
    def generate_structured(self, system_prompt, user_prompt, response_model, **kwargs):
        return RawEvaluation(
            relevance_score=0.8,
            correctness_score=0.9,
            depth_score=0.8,
            clarity_score=0.9,
            overall_score=0.85,
            strengths=["Good"],
            weaknesses=[],
            evidence_summary="Good job",
            qualitative_coverage_signal=CoverageSignal.PARTIALLY_COVERED,
            follow_up_signal=FollowUpSignal.NONE
        )
        
    def generate_text(self, *args, **kwargs):
        return "mock text"


def test_llm_answer_evaluator_success_path():
    provider = MockSuccessProvider()
    evaluator = LLMAnswerEvaluator(provider=provider)
    
    req = EvaluationRequest(
        session_id="s1",
        question_record_id="q1",
        topic_id="t1",
        topic_name="Python",
        question_text="What is it?",
        question_type=QuestionType.INITIAL,
        difficulty=DifficultyLevel.EASY,
        candidate_answer="A language.",
        interview_mode_criteria={"technical": "must be correct"},
        relevant_candidate_context=[]
    )
    
    res = evaluator.evaluate(req)
    assert res.overall_score == 0.85
    assert res.qualitative_coverage_signal == CoverageSignal.PARTIALLY_COVERED


def _make_request():
    return EvaluationRequest(
        session_id="s1",
        question_record_id="q1",
        topic_id="t1",
        topic_name="Python",
        question_text="What is it?",
        question_type=QuestionType.INITIAL,
        difficulty=DifficultyLevel.EASY,
        candidate_answer="A language.",
        interview_mode_criteria={"technical": "must be correct"},
        relevant_candidate_context=[]
    )


def test_llm_answer_evaluator_retries_transient_error_with_backoff(monkeypatch):
    """
    Same shared-quota issue as question generation (see
    llm_question_generator.py): evaluation calls hit the real account's HTTP
    429 rate_limit_exceeded, and previously had zero internal retry/backoff,
    relying entirely on AnswerEngine's own outer loop, which retried
    immediately against the same still-active rate-limit window. This proves
    evaluate() now retries a transient failure itself, with a real delay,
    via the existing (previously unused) ResiliencePolicy.
    """
    from unittest.mock import MagicMock
    from app.ai_interview.llm_infrastructure.exceptions import LLMTransientError

    sleep_calls = []
    monkeypatch.setattr("app.ai_interview.llm_infrastructure.resilience.time.sleep", lambda s: sleep_calls.append(s))

    mock_provider = MagicMock()
    mock_provider.generate_structured.side_effect = [
        LLMTransientError("429 - rate_limit_exceeded"),
        RawEvaluation(
            relevance_score=0.8, correctness_score=0.8, depth_score=0.8, clarity_score=0.8,
            overall_score=0.8, strengths=["Good"], weaknesses=[], evidence_summary="Solid.",
            qualitative_coverage_signal=CoverageSignal.PARTIALLY_COVERED, follow_up_signal=FollowUpSignal.NONE,
        ),
    ]
    evaluator = LLMAnswerEvaluator(provider=mock_provider)

    result = evaluator.evaluate(_make_request())

    assert result.overall_score == 0.8
    assert mock_provider.generate_structured.call_count == 2
    assert sleep_calls == [2.0]


def test_llm_answer_evaluator_does_not_retry_fatal_error_internally():
    """A fatal provider error must propagate immediately (exactly one call),
    so AnswerEngine's own outer retry loop decides whether to try again --
    not a duplicated retry layer inside evaluate() itself."""
    from unittest.mock import MagicMock
    from app.ai_interview.llm_infrastructure.exceptions import LLMFatalError
    from app.ai_interview.answer_engine.exceptions import EvaluationValidationError

    mock_provider = MagicMock()
    mock_provider.generate_structured.side_effect = LLMFatalError("400 - json_validate_failed")
    evaluator = LLMAnswerEvaluator(provider=mock_provider)

    with pytest.raises(EvaluationValidationError):
        evaluator.evaluate(_make_request())

    assert mock_provider.generate_structured.call_count == 1
