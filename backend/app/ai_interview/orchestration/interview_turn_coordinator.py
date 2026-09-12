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
                
            eval_result = self.answer_engine.evaluate_answer(
                submission=answer_submission,
                session=session,
                mode=mode
            )
            evaluation_record = session.evaluation_history[-1] if session.evaluation_history else None
            
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
            RuntimeController.execute_transition(session, decision.allowed_action)
            # If we just advanced topic, we need to mark it IN_PROGRESS.
            if decision.allowed_action == RuntimeAction.ADVANCE_TOPIC and session.current_topic_id:
                active_topic = next((t for t in session.topic_progress if t.topic_id == session.current_topic_id), None)
                if active_topic:
                    TopicStateManager.mark_in_progress(active_topic)
            decision = RuntimeController.get_allowed_action(session)
            
        if decision.allowed_action == RuntimeAction.COMPLETE:
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
