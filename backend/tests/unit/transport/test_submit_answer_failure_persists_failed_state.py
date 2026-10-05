"""
Regression: real-provider end-to-end verification (Task 7).

When question generation fails after a successful evaluation, handle_submit_answer
moves the session to FAILED and saves it. It did so while generation_claim was
still set, which SessionPersistenceValidator rejects for a terminal session
(invariant 1), so save() raised PersistenceInvariantError: the FAILED state was
never persisted and the client got PERSISTENCE_FAILED instead of
GENERATION_FAILED.

The existing mocked-repo test cannot see this (a mock save never validates), so
this one runs the REAL validator on whatever object the service saves.
"""
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

import app.ai_interview.schemas.session  # noqa: F401  (avoid circular import)
from app.ai_interview.answer_engine.enums import CoverageSignal, FollowUpSignal
from app.ai_interview.answer_engine.schemas import EvaluationRecord
from app.ai_interview.core.enums import DifficultyLevel, InterviewState, QuestionType
from app.ai_interview.orchestration.interview_turn_coordinator import InterviewTurnResult
from app.ai_interview.persistence.validator import SessionPersistenceValidator
from app.ai_interview.question_engine.enums import QuestionStatus
from app.ai_interview.question_engine.schemas import QuestionRecord
from app.ai_interview.runtime.enums import RuntimeAction
from app.ai_interview.schemas.blueprint import InterviewBlueprint, TopicBlueprint
from app.ai_interview.schemas.interview_mode import InterviewModeDefinition
from app.ai_interview.schemas.session import InterviewSessionSchema, OperationClaim
from app.ai_interview.transport.schemas.ws_commands import SubmitAnswerCommand
from app.ai_interview.transport.services.interview_transport_service import InterviewTransportService


def _claim(claim_id):
    now = datetime.now(timezone.utc)
    return OperationClaim(claim_id=claim_id, claimed_at=now, expires_at=now + timedelta(seconds=60))


@pytest.mark.asyncio
async def test_generation_failure_saves_a_session_that_passes_persistence_validation():
    now = datetime.now(timezone.utc)
    eval_claim, gen_claim = _claim("eval-claim"), _claim("gen-claim")

    question = QuestionRecord(
        session_id="s1", turn_number=1, record_id="q1", topic_id="t1", question_text="Q",
        question_type=QuestionType.INITIAL, difficulty=DifficultyLevel.MEDIUM,
        status=QuestionStatus.DISPATCHED, evaluation_claim=eval_claim)
    evaluation = EvaluationRecord(
        evaluation_id="ev1", question_record_id="q1", topic_id="t1", overall_score=0.2,
        qualitative_coverage_signal=CoverageSignal.NOT_COVERED,
        follow_up_signal=FollowUpSignal.CLARIFICATION_MAY_HELP)
    session = InterviewSessionSchema(
        session_id="s1", candidate_id="c1", company_id="co", campaign_id="ca", mode_id="m1", mode_version=1,
        created_at=now, state=InterviewState.IN_PROGRESS, version=3, questions_asked_total=1,
        generation_claim=gen_claim, question_history=[question], evaluation_history=[evaluation],
        blueprint=InterviewBlueprint(mode_id="m1", blueprint_version="1", min_questions=1, max_questions=5,
                                     total_question_budget=5, emergency_max_questions=10, topics=[
            TopicBlueprint(topic_id="t1", topic_name="T1", source="resume", priority=1, mandatory=True,
                           question_budget=3)]))

    saved = []

    async def validating_save(sess, **kwargs):
        SessionPersistenceValidator.validate(sess)   # what the real repository.save() does first
        saved.append((sess.state, sess.generation_claim, [q.evaluation_claim for q in sess.question_history]))

    repo = AsyncMock()
    repo.get_by_id.return_value = session
    repo.claim_evaluation.return_value = eval_claim
    repo.claim_question_generation.return_value = gen_claim
    repo.save = AsyncMock(side_effect=validating_save)

    svc = InterviewTransportService(session_repo=repo, resume_repo=AsyncMock(), mode_repo=AsyncMock(),
                                    coordinator=MagicMock())
    svc._load_candidate_context = AsyncMock(return_value={})
    svc._load_mode = AsyncMock(return_value=InterviewModeDefinition(
        mode_id="m1", version=1, name="M", description="d", status="published", created_at=now, settings={}))

    turn_result = InterviewTurnResult(action=RuntimeAction.FAIL, evaluation=evaluation, interview_completed=False,
                                      waiting_for_answer=False, current_topic_id="t1", question=None)
    command = SubmitAnswerCommand(command_type="submit_answer", command_id="cmd1",
                                  payload={"question_record_id": "q1", "answer_text": "an answer"})

    with patch("app.ai_interview.transport.services.interview_transport_service.event_emitter",
               new_callable=AsyncMock) as emitter, \
         patch("app.ai_interview.transport.services.interview_transport_service.get_interview_executor"), \
         patch("asyncio.get_event_loop") as get_loop:
        loop = AsyncMock()
        loop.run_in_executor = AsyncMock(return_value=turn_result)
        get_loop.return_value = loop

        await svc.handle_submit_answer("s1", command, MagicMock())

    assert saved == [(InterviewState.FAILED, None, [None])]
    assert emitter.emit_error.call_args[0][1].code == "GENERATION_FAILED"   # not PERSISTENCE_FAILED
    assert repo.save.call_args.kwargs["generation_fencing_id"] == "gen-claim"
    assert repo.save.call_args.kwargs["evaluation_fencing_id"] == "eval-claim"
