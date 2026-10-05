import pytest
from unittest.mock import MagicMock, patch
from app.ai_interview.orchestration.interview_turn_coordinator import InterviewTurnCoordinator
from app.ai_interview.schemas.session import InterviewSessionSchema, TopicProgress
from app.ai_interview.question_engine.schemas import QuestionRecord
from app.ai_interview.core.enums import InterviewState, QuestionType, DifficultyLevel, TopicState
from app.ai_interview.question_engine.enums import QuestionStatus
from app.ai_interview.answer_engine.schemas import AnswerSubmission
from app.ai_interview.schemas.interview_mode import InterviewModeDefinition
from app.ai_interview.runtime.enums import RuntimeAction

def build_test_session(mode_id="practice", state=InterviewState.IN_PROGRESS):
    session = MagicMock(spec=InterviewSessionSchema)
    session.session_id = "test-session"
    session.mode_id = mode_id
    session.state = state
    
    q_id = "q1"
    session.question_history = [
        QuestionRecord(
            record_id=q_id,
            session_id=session.session_id,
            turn_number=1,
            topic_id="t1",
            question_text="Q",
            question_type=QuestionType.INITIAL,
            difficulty=DifficultyLevel.EASY,
            status=QuestionStatus.DISPATCHED
        )
    ]
    
    tp = MagicMock(spec=TopicProgress)
    tp.topic_id = "t1"
    tp.state = TopicState.IN_PROGRESS
    tp.questions_asked = 0
    tp.qualitatively_covered = False
    tp.structurally_attempted = False
    
    tp.follow_up_count = 0
    session.topic_progress = [tp]
    session.evaluation_history = []
    
    budget = MagicMock(topic_id="t1", question_budget=3, time_budget_seconds=100)
    session.blueprint = MagicMock()
    session.blueprint.topics = [budget]
    session.current_topic_id = "t1"
    return session, q_id

def test_a_practice_answer_skips_evaluation():
    q_engine = MagicMock()
    a_engine = MagicMock()
    
    # Don't mock out the runtime controller's decisions fully, 
    # but patch it to return something predictable
    with patch("app.ai_interview.orchestration.interview_turn_coordinator.RuntimeController") as rc:
        rc.get_allowed_action.return_value = MagicMock(allowed_action=RuntimeAction.NO_ACTION)
        
        coordinator = InterviewTurnCoordinator(q_engine, a_engine)
        
        qr = QuestionRecord(
            record_id="q2",
            session_id="test-session",
            turn_number=2,
            topic_id="t1",
            question_text="Q2",
            question_type=QuestionType.FOLLOW_UP,
            difficulty=DifficultyLevel.EASY,
            status=QuestionStatus.DISPATCHED
        )
        q_engine.request_next_question.return_value = MagicMock(success=True, question_record=qr)
        
        session, q_id = build_test_session("practice")
        
        submission = AnswerSubmission(
            session_id=session.session_id,
            question_record_id=q_id,
            answer_text="Practice text"
        )
        
        mode = MagicMock(spec=InterviewModeDefinition)
        
        coordinator.advance_interview(session, None, mode, submission)
        
        # Assert A
        a_engine.evaluate_answer.assert_not_called()
        assert session.question_history[0].status == QuestionStatus.EVALUATED
        assert session.topic_progress[0].questions_asked == 1
        assert session.topic_progress[0].structurally_attempted == True
        assert session.topic_progress[0].qualitatively_covered == True

def test_c_official_answer_still_evaluates():
    q_engine = MagicMock()
    a_engine = MagicMock()
    
    with patch("app.ai_interview.orchestration.interview_turn_coordinator.RuntimeController") as rc, \
         patch("app.ai_interview.orchestration.interview_turn_coordinator.TopicStateManager") as tsm:
         
        rc.get_allowed_action.return_value = MagicMock(allowed_action=RuntimeAction.NO_ACTION)
        
        coordinator = InterviewTurnCoordinator(q_engine, a_engine)
        
        qr = QuestionRecord(
            record_id="q2",
            session_id="test-session",
            turn_number=2,
            topic_id="t1",
            question_text="Q2",
            question_type=QuestionType.FOLLOW_UP,
            difficulty=DifficultyLevel.EASY,
            status=QuestionStatus.DISPATCHED
        )
        q_engine.request_next_question.return_value = MagicMock(success=True, question_record=qr)
        
        session, q_id = build_test_session("standard")
        
        submission = AnswerSubmission(
            session_id=session.session_id,
            question_record_id=q_id,
            answer_text="Official text"
        )
        
        mode = MagicMock(spec=InterviewModeDefinition)
        
        # Fake evaluation result
        eval_result = MagicMock()
        eval_result.topic_id = "t1"
        a_engine.evaluate_answer.return_value = eval_result
        
        coordinator.advance_interview(session, None, mode, submission)
        
        # Assert C
        a_engine.evaluate_answer.assert_called_once()
