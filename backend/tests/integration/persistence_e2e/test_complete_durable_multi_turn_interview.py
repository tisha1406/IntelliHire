import pytest
from datetime import datetime, timezone
import uuid

from app.ai_interview.schemas.blueprint import InterviewBlueprint
from app.ai_interview.schemas.session import InterviewSessionSchema, OperationClaim
from app.ai_interview.question_engine.schemas import QuestionRecord, QuestionStatus, QuestionType, DifficultyLevel
from app.ai_interview.answer_engine.schemas import EvaluationRecord, CoverageSignal, FollowUpSignal
from app.ai_interview.core.enums import InterviewState, TopicState
from app.ai_interview.runtime import SessionInitializer, RuntimeController, RuntimeAction

@pytest.mark.mongodb
@pytest.mark.asyncio
async def test_complete_durable_multi_turn_interview(real_repo):
    """
    Simulates a full end-to-end multi-turn interview using the real MongoDB repository.
    Verifies state machines, OCC versions, idempotency invariants, and topic progression.
    """
    # 1. Initialize Session (Phases 1-3 assumed complete, using mock blueprint)
    blueprint = InterviewBlueprint(
        blueprint_version="1.0",
        total_question_budget=2,
        min_questions=1,
        max_questions=2,
        emergency_max_questions=3,
        topics=[
            {
                "topic_id": "topic_1",
                "topic_name": "Python Fundamentals",
                "source": "resume",
                "priority": 10,
                "mandatory": True
            },
            {
                "topic_id": "topic_2",
                "topic_name": "System Design",
                "source": "resume",
                "priority": 5,
                "mandatory": True
            }
        ]
    )
    
    session_id = str(uuid.uuid4())
    session = SessionInitializer.initialize(
        blueprint=blueprint,
        candidate_id="cand_1",
        company_id="comp_1",
        campaign_id="camp_1",
        mode_id="mode_1",
        mode_version=1
    )
    session.session_id = session_id
    
    # Save initialized session
    await real_repo.save(session, expected_version=0)
    
    # Reload to verify
    reloaded_session = await real_repo.get_by_id(session_id)
    assert reloaded_session.version == 1
    assert reloaded_session.state == InterviewState.CREATED
    
    # 2. Runtime Transitions: Initialize, Start & Advance to Topic 1
    RuntimeController.execute_transition(reloaded_session, RuntimeAction.INITIALIZE)
    RuntimeController.execute_transition(reloaded_session, RuntimeAction.START)
    RuntimeController.execute_transition(reloaded_session, RuntimeAction.ADVANCE_TOPIC)
    
    assert reloaded_session.state == InterviewState.IN_PROGRESS
    assert reloaded_session.current_topic_id == "topic_1"
    
    await real_repo.save(reloaded_session, expected_version=1)
    
    # 3. Simulate Worker acquiring lease for Question 1
    session = await real_repo.get_by_id(session_id)
    claim = await real_repo.claim_question_generation(session.session_id, expected_version=session.version, lease_seconds=10)
    claim_id = claim.claim_id
    
    session = await real_repo.get_by_id(session_id)
    assert session.generation_claim is not None
    assert session.generation_claim.claim_id == claim_id
    
    # Generate Question 1
    q1_id = str(uuid.uuid4())
    q1 = QuestionRecord(
        record_id=q1_id,
        session_id=session.session_id,
        turn_number=1,
        topic_id="topic_1",
        question_text="What are lists?",
        question_type=QuestionType.INITIAL,
        difficulty=DifficultyLevel.MEDIUM,
        status=QuestionStatus.DISPATCHED
    )
    session.question_history.append(q1)
    session.questions_asked_total += 1
    
    # Update topic progress
    for topic in session.topic_progress:
        if topic.topic_id == "topic_1":
            topic.questions_asked += 1
            break
            
    # Finalize Generation
    session.generation_claim = None
    await real_repo.save(session, expected_version=session.version, generation_fencing_id=claim_id)
    
    # 4. Simulate Answer Submission & Evaluation 1
    session = await real_repo.get_by_id(session_id)
    assert session.questions_asked_total == 1
    
    eval_claim = await real_repo.claim_evaluation(session.session_id, q1_id, expected_version=session.version, lease_seconds=10)
    eval_claim_id = eval_claim.claim_id
    
    session = await real_repo.get_by_id(session_id)
    assert session.question_history[-1].evaluation_claim is not None
    assert session.question_history[-1].evaluation_claim.claim_id == eval_claim_id
    
    eval1 = EvaluationRecord(
        evaluation_id=str(uuid.uuid4()),
        question_record_id=q1_id,
        topic_id="topic_1",
        overall_score=0.8,
        qualitative_coverage_signal=CoverageSignal.QUALITATIVELY_COVERED,
        follow_up_signal=FollowUpSignal.NONE
    )
    session.evaluation_history.append(eval1)
    session.question_history[-1].status = QuestionStatus.EVALUATED
    session.question_history[-1].evaluation_claim = None
    
    for topic in session.topic_progress:
        if topic.topic_id == "topic_1":
            topic.coverage_score += 0.8
            topic.structurally_attempted = True
            topic.qualitatively_covered = True
            topic.state = TopicState.COVERED # Simulating budget exhausted or coverage met
            break
            
    await real_repo.save(session, expected_version=session.version, evaluation_fencing_id=eval_claim_id)
    
    # 5. Advance to Topic 2
    session = await real_repo.get_by_id(session_id)
    RuntimeController.execute_transition(session, RuntimeAction.ADVANCE_TOPIC)
    assert session.current_topic_id == "topic_2"
    await real_repo.save(session, expected_version=session.version)
    
    # 6. Generate Question 2 (Topic 2)
    session = await real_repo.get_by_id(session_id)
    claim_2 = await real_repo.claim_question_generation(session.session_id, expected_version=session.version)
    claim_id_2 = claim_2.claim_id
    session = await real_repo.get_by_id(session_id)
    
    q2_id = str(uuid.uuid4())
    q2 = QuestionRecord(
        record_id=q2_id,
        session_id=session.session_id,
        turn_number=2,
        topic_id="topic_2",
        question_text="Design Twitter.",
        question_type=QuestionType.INITIAL,
        difficulty=DifficultyLevel.HARD,
        status=QuestionStatus.DISPATCHED
    )
    session.question_history.append(q2)
    session.questions_asked_total += 1
    for topic in session.topic_progress:
        if topic.topic_id == "topic_2":
            topic.questions_asked += 1
            break
    session.generation_claim = None
    await real_repo.save(session, expected_version=session.version, generation_fencing_id=claim_id_2)
    
    # 7. Evaluate Question 2
    session = await real_repo.get_by_id(session_id)
    eval_claim_2_obj = await real_repo.claim_evaluation(session.session_id, q2_id, expected_version=session.version)
    eval_claim_2 = eval_claim_2_obj.claim_id
    session = await real_repo.get_by_id(session_id)
    
    eval2 = EvaluationRecord(
        evaluation_id=str(uuid.uuid4()),
        question_record_id=q2_id,
        topic_id="topic_2",
        overall_score=0.9,
        qualitative_coverage_signal=CoverageSignal.QUALITATIVELY_COVERED,
        follow_up_signal=FollowUpSignal.NONE
    )
    session.evaluation_history.append(eval2)
    session.question_history[-1].status = QuestionStatus.EVALUATED
    session.question_history[-1].evaluation_claim = None
    
    for topic in session.topic_progress:
        if topic.topic_id == "topic_2":
            topic.coverage_score += 0.95
            topic.structurally_attempted = True
            topic.qualitatively_covered = True
            topic.state = TopicState.COVERED # Finished topic 2
            break
            
    await real_repo.save(session, expected_version=session.version, evaluation_fencing_id=eval_claim_2)
    
    # 8. Complete Interview
    session = await real_repo.get_by_id(session_id)
    RuntimeController.execute_transition(session, RuntimeAction.COMPLETE)
    assert session.state == InterviewState.COMPLETED
    await real_repo.save(session, expected_version=session.version)
    
    # 9. Final Invariant Checks
    final_session = await real_repo.get_by_id(session_id)
    assert final_session.questions_asked_total == 2
    assert len(final_session.question_history) == 2
    assert len(final_session.evaluation_history) == 2
    assert final_session.generation_claim is None
    for q in final_session.question_history:
        assert q.evaluation_claim is None
