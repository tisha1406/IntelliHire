from app.ai_interview.schemas.session import InterviewSessionSchema
from app.ai_interview.schemas.interview_mode import InterviewModeDefinition
from app.ai_interview.answer_engine.schemas import AnswerSubmission, ProcessedAnswer, EvaluationRequest
from app.ai_interview.answer_engine.exceptions import QuestionCorrelationError

class EvaluationRequestBuilder:
    """
    Correlates the candidate's answer with the exact authoritative QuestionRecord
    and builds the EvaluationRequest for the AnswerEvaluator.
    """
    
    @staticmethod
    def build(
        submission: AnswerSubmission,
        processed_answer: ProcessedAnswer,
        session: InterviewSessionSchema,
        mode: InterviewModeDefinition
    ) -> EvaluationRequest:
        
        # 1. Validate session correlation
        if submission.session_id != session.session_id:
            raise QuestionCorrelationError(f"Answer belongs to session {submission.session_id}, not {session.session_id}")
            
        # 2. Look up the QuestionRecord
        question_record = next(
            (q for q in session.question_history if q.record_id == submission.question_record_id),
            None
        )
        if not question_record:
            raise QuestionCorrelationError(f"Question record {submission.question_record_id} not found in session history.")
            
        # 3. Duplicate evaluation protection (Idempotency)
        already_evaluated = any(
            e.question_record_id == submission.question_record_id for e in session.evaluation_history
        )
        if already_evaluated:
            raise QuestionCorrelationError(f"Question {submission.question_record_id} has already been evaluated.")
            
        # 4. Construct Mode Criteria
        criteria = {
            "focus_areas": "General correctness and clarity", 
            "difficulty_policy": mode.settings.difficulty_policy
        }
        
        # Adjust criteria based on mode
        if "Technical" in mode.name or "technical" in mode.settings.allowed_question_types:
            criteria["focus_areas"] = "Technical correctness, Problem-solving, Conceptual depth"
        elif "Behavioral" in mode.name or "behavioral" in mode.settings.allowed_question_types:
            criteria["focus_areas"] = "Relevance, STAR structure, Communication, Reflection"
            
        topic_name = next(
            (t.topic_name for t in session.blueprint.topics if t.topic_id == question_record.topic_id), 
            question_record.topic_id
        )

        return EvaluationRequest(
            session_id=session.session_id,
            question_record_id=question_record.record_id,
            topic_id=question_record.topic_id,
            topic_name=topic_name,
            question_text=question_record.question_text,
            question_type=question_record.question_type,
            difficulty=question_record.difficulty,
            candidate_answer=processed_answer.normalized_text,
            interview_mode_criteria=criteria,
            relevant_candidate_context=[]
        )
