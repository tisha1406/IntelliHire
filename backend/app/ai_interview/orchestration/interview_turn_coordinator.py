from typing import Optional
from app.ai_interview.schemas.session import InterviewSessionSchema
from app.ai_interview.schemas.interview_mode import InterviewModeDefinition
from app.ai_interview.resume_processing.schemas import CandidateInterviewContext
from app.ai_interview.runtime.runtime_controller import RuntimeController
from app.ai_interview.runtime.enums import RuntimeAction
from app.ai_interview.core.enums import InterviewState, TopicState
from app.ai_interview.question_engine.question_engine import QuestionEngine
from app.ai_interview.answer_engine.answer_engine import AnswerEngine
from app.ai_interview.answer_engine.schemas import AnswerSubmission
from app.ai_interview.orchestration.schemas import InterviewTurnResult
from app.ai_interview.runtime.topic_state_manager import TopicStateManager
from app.ai_interview.question_engine.enums import QuestionStatus
import logging

logger = logging.getLogger(__name__)

class InterviewTurnCoordinator:
    """
    Coordinates exactly one interview turn (action -> next state).
    It orchestrates RuntimeController, QuestionEngine, and AnswerEngine
    without harboring core business logic itself.
    """
    
    def __init__(self, question_engine: QuestionEngine, answer_engine: AnswerEngine):
        self.question_engine = question_engine
        self.answer_engine = answer_engine

    def advance_interview(
        self,
        session: InterviewSessionSchema,
        candidate_context: CandidateInterviewContext,
        mode: InterviewModeDefinition,
        answer_submission: Optional[AnswerSubmission] = None
    ) -> InterviewTurnResult:
        
        evaluation_record = None
        
        # 1. If an answer was submitted, evaluate it first
        if answer_submission:
            if session.state in {InterviewState.COMPLETED, InterviewState.FAILED}:
                from app.ai_interview.answer_engine.exceptions import AnswerEvaluationError
                raise AnswerEvaluationError("Cannot evaluate answer for a terminal interview session.")
                
            if session.mode_id == "practice":
                logger.info(f"[INTERVIEW] PRACTICE_EVALUATION_SKIPPED session={session.session_id} question={answer_submission.question_record_id} reason=practice_mode")
                
                question_record = next((q for q in session.question_history if q.record_id == answer_submission.question_record_id), None)
                if question_record:
                    question_record.status = QuestionStatus.EVALUATED
                    topic_id = question_record.topic_id
                else:
                    topic_id = None
                
                evaluation_record = None
                
                if topic_id:
                    topic_prog = next((t for t in session.topic_progress if t.topic_id == topic_id), None)
                    if topic_prog:
                        topic_prog.questions_asked += 1
                        
                        # In practice mode, one answer is sufficient to cover the topic
                        if topic_prog.state == TopicState.IN_PROGRESS:
                            topic_prog.structurally_attempted = True
                            topic_prog.qualitatively_covered = True
                            TopicStateManager.attempt_cover(topic_prog)
            else:
                logger.info(f"[INTERVIEW] OFFICIAL_EVALUATION_STARTED session={session.session_id} question={answer_submission.question_record_id}")
                eval_result = self.answer_engine.evaluate_answer(
                    submission=answer_submission,
                    session=session,
                    mode=mode
                )
                evaluation_record = session.evaluation_history[-1] if session.evaluation_history else None
                logger.info(f"[INTERVIEW] OFFICIAL_EVALUATION_COMPLETED session={session.session_id} question={answer_submission.question_record_id} status=completed score={evaluation_record.overall_score if evaluation_record else 0}")
                
                # 2. Re-assess topic state deterministically after evaluation
                topic_prog = next((t for t in session.topic_progress if t.topic_id == eval_result.topic_id), None)
                topic_budget = next((t.question_budget for t in session.blueprint.topics if t.topic_id == eval_result.topic_id), 0)
                
                if topic_prog and topic_prog.state == TopicState.IN_PROGRESS:
                    if topic_prog.qualitatively_covered:
                        topic_prog.structurally_attempted = True
                        TopicStateManager.attempt_cover(topic_prog)
                    elif topic_prog.questions_asked >= topic_budget:
                        # Budget exhausted, but not covered -> abandon it so interview can proceed
                        TopicStateManager.mark_failed_abandoned(topic_prog)

        # 3. Ask RuntimeController what to do next
        decision = RuntimeController.get_allowed_action(session)
        
        # Keep advancing state deterministically if we are INITIALIZE or START
        while decision.allowed_action in [RuntimeAction.INITIALIZE, RuntimeAction.START, RuntimeAction.ADVANCE_TOPIC]:
            previous_topic_id = session.current_topic_id
            RuntimeController.execute_transition(session, decision.allowed_action)
            
            # If we just advanced topic, we need to mark it IN_PROGRESS and handle difficulty initialization/reset
            if decision.allowed_action == RuntimeAction.ADVANCE_TOPIC and session.current_topic_id:
                active_topic = next((t for t in session.topic_progress if t.topic_id == session.current_topic_id), None)
                if active_topic:
                    TopicStateManager.mark_in_progress(active_topic)
                    
                    if session.mode_id != "practice":
                        from app.ai_interview.runtime.adaptive_difficulty_engine import AdaptiveDifficultyEngine
                        AdaptiveDifficultyEngine.handle_topic_switch(
                            session=session,
                            topic_progress=active_topic,
                            previous_topic_id=previous_topic_id,
                            strategy=session.strategy_snapshot
                        )
                        
            decision = RuntimeController.get_allowed_action(session)
            
        if decision.allowed_action == RuntimeAction.COMPLETE:
            logger.info(f"[INTERVIEW] INTERVIEW_COMPLETION_DECIDED session={session.session_id} mode={session.mode_id} reason=complete_action")
            # Persist the deterministic completion reason before the state transition
            if decision.completion_reason is not None:
                session.completion_reason = decision.completion_reason
            RuntimeController.execute_transition(session, RuntimeAction.COMPLETE)
            return InterviewTurnResult(
                action=RuntimeAction.COMPLETE,
                evaluation=evaluation_record,
                interview_completed=True,
                waiting_for_answer=False,
                current_topic_id=session.current_topic_id
            )
            
        if decision.allowed_action == RuntimeAction.NO_ACTION:
            # Question is permitted and interview is in progress
            if session.state == InterviewState.IN_PROGRESS and session.current_topic_id:
                question_result = self.question_engine.request_next_question(
                    session=session,
                    runtime_decision=decision,
                    candidate_context=candidate_context,
                    mode=mode
                )
                if question_result.success:
                    logger.info(f"[INTERVIEW] NEXT_QUESTION_SELECTED session={session.session_id} mode={session.mode_id} question={question_result.question_record.record_id} turn={question_result.question_record.turn_number}")
                    return InterviewTurnResult(
                        action=RuntimeAction.NO_ACTION, # Or a custom action like ASK_QUESTION
                        question=question_result.question_record,
                        evaluation=evaluation_record,
                        interview_completed=False,
                        waiting_for_answer=True,
                        current_topic_id=session.current_topic_id
                    )
                else:
                    # Generator failed completely
                    return InterviewTurnResult(
                        action=RuntimeAction.FAIL,
                        evaluation=evaluation_record,
                        interview_completed=False,
                        waiting_for_answer=False,
                        current_topic_id=session.current_topic_id
                    )
                    
        return InterviewTurnResult(
            action=decision.allowed_action,
            evaluation=evaluation_record,
            interview_completed=(session.state == InterviewState.COMPLETED),
            waiting_for_answer=False,
            current_topic_id=session.current_topic_id
        )
