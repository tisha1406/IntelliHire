import logging
from app.ai_interview.schemas.session import InterviewSessionSchema
from app.ai_interview.schemas.interview_mode import InterviewModeDefinition
from app.ai_interview.answer_engine.schemas import AnswerSubmission, EvaluationResult
from app.ai_interview.answer_engine.config import MAX_EVALUATION_ATTEMPTS
from app.ai_interview.answer_engine.answer_processor import AnswerProcessor
from app.ai_interview.answer_engine.evaluation_request_builder import EvaluationRequestBuilder
from app.ai_interview.answer_engine.answer_evaluator import AnswerEvaluator
from app.ai_interview.answer_engine.evaluation_validator import EvaluationValidator
from app.ai_interview.answer_engine.evaluation_normalizer import EvaluationNormalizer
from app.ai_interview.answer_engine.coverage_assessor import CoverageAssessor
from app.ai_interview.answer_engine.evaluation_applicator import EvaluationApplicator
from app.ai_interview.answer_engine.exceptions import (
    AnswerValidationError, QuestionCorrelationError,
    EvaluationValidationError, AnswerEvaluationError,
    EvaluationApplicationError
)

logger = logging.getLogger(__name__)

class AnswerEngine:
    """
    Facade for the Answer Processing and Evaluation Engine (Phase 6).
    Coordinates deterministic evaluation pipeline.
    """
    def __init__(self, evaluator: AnswerEvaluator):
        self.evaluator = evaluator

    def evaluate_answer(
        self,
        submission: AnswerSubmission,
        session: InterviewSessionSchema,
        mode: InterviewModeDefinition
    ) -> EvaluationResult:
        
        # 1. Deterministic text processing & validation
        processed = AnswerProcessor.process(submission)
        
        # 2. Build explicit contextual request
        request = EvaluationRequestBuilder.build(submission, processed, session, mode)
        
        topic_progress = next((t for t in session.topic_progress if t.topic_id == request.topic_id), None)
        if not topic_progress:
            raise QuestionCorrelationError(f"Topic {request.topic_id} not found in session topic_progress.")
            
        # Fallback budget lookup
        topic_budget = next((t.question_budget for t in session.blueprint.topics if t.topic_id == request.topic_id), 0)
        
        # Find QuestionRecord to enforce lifecycle
        question_record = next((q for q in session.question_history if q.record_id == request.question_record_id), None)
        if question_record:
            # We don't fail if it's missing here, EvaluationRequestBuilder already validates correlation
            question_record.status = "evaluation_pending"
            
        # 3. Evaluator loop (Retry safely on transient / validation errors)
        raw_evaluation = None
        for attempt in range(1, MAX_EVALUATION_ATTEMPTS + 1):
            try:
                raw_evaluation = self.evaluator.evaluate(request)
                EvaluationValidator.validate(raw_evaluation)
                break # Success!
            except (EvaluationValidationError, RuntimeError) as e:
                logger.warning(f"Evaluation attempt {attempt} failed: {e}")
                if attempt == MAX_EVALUATION_ATTEMPTS:
                    raise AnswerEvaluationError(f"Failed to generate valid evaluation after {MAX_EVALUATION_ATTEMPTS} attempts: {e}")
                    
        if not raw_evaluation:
            raise AnswerEvaluationError("Evaluation loop completed without producing a result.")
            
        # 4. Normalize
        result = EvaluationNormalizer.normalize(raw_evaluation, request)
        
        # 5. Assess Topic Coverage
        assessment = CoverageAssessor.assess(
            topic_progress.evaluation_aggregate,
            result,
            topic_progress,
            topic_budget
        )
        
        # 6. Apply safely (Rolls back if failure occurs)
        EvaluationApplicator.apply(session, topic_progress, result, assessment)
        
        if question_record:
            question_record.status = "evaluated"
            
        return result
