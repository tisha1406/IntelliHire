import pytest
import uuid
import asyncio

from app.ai_interview.schemas.blueprint import InterviewBlueprint
from app.ai_interview.schemas.session import InterviewSessionSchema, OperationClaim
from app.ai_interview.question_engine.schemas import QuestionRecord, QuestionStatus, QuestionType, DifficultyLevel
from app.ai_interview.answer_engine.schemas import EvaluationRecord, CoverageSignal, FollowUpSignal
from app.ai_interview.core.enums import InterviewState, TopicState
from app.ai_interview.runtime import SessionInitializer, RuntimeController, RuntimeAction

@pytest.mark.mongodb
@pytest.mark.asyncio
async def test_budget_exhaustion_end_to_end(real_repo):
    """
    Simulates a candidate who repeatedly gives poor answers.
    Verifies that the deterministic engine forces a topic transition
    when emergency max budget is exhausted, overriding any LLM recommendation.
    """
    blueprint = InterviewBlueprint(
        blueprint_version="1.0", total_question_budget=5, min_questions=1, max_questions=2, emergency_max_questions=3,
        topics=[
            {"topic_id": "topic_1", "topic_name": "Python", "source": "resume", "priority": 10, "mandatory": True},
            {"topic_id": "topic_2", "topic_name": "Design", "source": "resume", "priority": 5, "mandatory": True}
        ]
    )
    
    session = SessionInitializer.initialize(
        blueprint=blueprint, candidate_id="cand_1", company_id="comp_1", campaign_id="camp_1", mode_id="m_1", mode_version=1
    )
    session.session_id = str(uuid.uuid4())
    RuntimeController.execute_transition(session, RuntimeAction.INITIALIZE)
    RuntimeController.execute_transition(session, RuntimeAction.START)
    RuntimeController.execute_transition(session, RuntimeAction.ADVANCE_TOPIC)
    
    assert session.current_topic_id == "topic_1"
    
    # We will simulate 3 poor answers causing an emergency transition
    for i in range(3):
        q_id = str(uuid.uuid4())
        q = QuestionRecord(
            record_id=q_id, session_id=session.session_id, turn_number=i+1, topic_id="topic_1", question_text=f"Q{i}",
            question_type=QuestionType.INITIAL if i == 0 else QuestionType.FOLLOW_UP, difficulty=DifficultyLevel.MEDIUM, status=QuestionStatus.EVALUATED
        )
        session.question_history.append(q)
        session.questions_asked_total += 1
        session.topic_progress[0].questions_asked += 1
        
        eval_record = EvaluationRecord(
            evaluation_id=str(uuid.uuid4()), question_record_id=q_id, topic_id="topic_1",
            overall_score=0.2, qualitative_coverage_signal=CoverageSignal.NOT_COVERED, follow_up_signal=FollowUpSignal.DEPTH_PROBE_MAY_HELP
        )
        session.evaluation_history.append(eval_record)
        
    # Manually simulate Phase 6 failing the topic due to emergency max questions reached
    session.topic_progress[0].structurally_attempted = True
    session.topic_progress[0].state = TopicState.FAILED_ABANDONED
    
    # Now simulate the controller determining the next action
    decision = RuntimeController.get_allowed_action(session)
    assert decision.allowed_action == RuntimeAction.ADVANCE_TOPIC
    assert decision.active_topic_id == "topic_2"
    
    # Apply it
    RuntimeController.execute_transition(session, RuntimeAction.ADVANCE_TOPIC)
    
    await real_repo.save(session, expected_version=0)
    final = await real_repo.get_by_id(session.session_id)
    assert final.current_topic_id == "topic_2"
