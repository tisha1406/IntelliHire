import pytest
import uuid

from app.ai_interview.schemas.blueprint import InterviewBlueprint
from app.ai_interview.schemas.session import InterviewSessionSchema
from app.ai_interview.question_engine.schemas import QuestionRecord, QuestionStatus, QuestionType, DifficultyLevel
from app.ai_interview.core.enums import InterviewState, TopicState
from app.ai_interview.runtime import SessionInitializer, RuntimeController, RuntimeAction

@pytest.mark.mongodb
@pytest.mark.asyncio
async def test_session_restart_recovery(real_repo):
    """
    Simulates a worker dying and a brand new process taking over, 
    reloading the session from MongoDB and seamlessly continuing.
    """
    blueprint = InterviewBlueprint(
        blueprint_version="1.0",
        total_question_budget=5,
        min_questions=2,
        max_questions=5,
        emergency_max_questions=7,
        topics=[
            {
                "topic_id": "topic_1",
                "topic_name": "Databases",
                "source": "resume",
                "priority": 1
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
    
    RuntimeController.execute_transition(session, RuntimeAction.INITIALIZE)
    RuntimeController.execute_transition(session, RuntimeAction.START)
    RuntimeController.execute_transition(session, RuntimeAction.ADVANCE_TOPIC)
    
    q1 = QuestionRecord(
        record_id=str(uuid.uuid4()),
        session_id=session.session_id,
        turn_number=1,
        topic_id="topic_1",
        question_text="Explain ACID.",
        question_type=QuestionType.INITIAL,
        difficulty=DifficultyLevel.MEDIUM,
        status=QuestionStatus.DISPATCHED
    )
    session.question_history.append(q1)
    session.questions_asked_total += 1
    session.topic_progress[0].questions_asked += 1
    session.topic_progress[0].state = TopicState.IN_PROGRESS
    
    # Save the session via worker A
    await real_repo.save(session, expected_version=0)
    
    # SIMULATE COMPLETE PROCESS RESTART
    # We explicitly wipe out the `session` variable to prove no python-memory is shared
    del session
    
    # Worker B spins up and loads the document from MongoDB
    reloaded = await real_repo.get_by_id(session_id)
    
    # Verify the Pydantic type reconstruction is flawless
    assert isinstance(reloaded, InterviewSessionSchema)
    assert reloaded.version == 1
    assert reloaded.state == InterviewState.IN_PROGRESS
    assert reloaded.current_topic_id == "topic_1"
    
    assert len(reloaded.question_history) == 1
    assert isinstance(reloaded.question_history[0], QuestionRecord)
    assert reloaded.question_history[0].question_text == "Explain ACID."
    assert reloaded.questions_asked_total == 1
    
    assert isinstance(reloaded.blueprint, InterviewBlueprint)
    assert reloaded.topic_progress[0].state == TopicState.IN_PROGRESS
    
    # Worker B continues the interview by evaluating the question
    reloaded.question_history[0].status = QuestionStatus.ANSWER_RECEIVED
    await real_repo.save(reloaded, expected_version=reloaded.version)
    
    # Verify persistence worked for Worker B
    final = await real_repo.get_by_id(session_id)
    assert final.version == 2
    assert final.question_history[0].status == QuestionStatus.ANSWER_RECEIVED
