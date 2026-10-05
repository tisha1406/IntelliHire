import copy
from app.ai_interview.schemas.session import InterviewSessionSchema, TopicProgress
from app.ai_interview.answer_engine.schemas import EvaluationResult, EvaluationRecord
from app.ai_interview.answer_engine.coverage_assessor import CoverageAssessment
from app.ai_interview.answer_engine.exceptions import EvaluationApplicationError

class EvaluationApplicator:
    """
    Safely applies evaluation results to the deterministic session.
    Guarantees complete rollback if any mutation step fails.
    """
    
    @staticmethod
    def apply(
        session: InterviewSessionSchema,
        topic_progress: TopicProgress,
        evaluation: EvaluationResult,
        coverage_assessment: CoverageAssessment
    ) -> None:
        
        # 1. Enforce Application-Level Idempotency (Duplicate detection)
        for existing_record in session.evaluation_history:
            if existing_record.question_record_id == evaluation.question_record_id:
                raise EvaluationApplicationError(f"Duplicate evaluation: question {evaluation.question_record_id} has already been evaluated.")

        # 2. Take a safe snapshot for rollback
        original_topic_progress = copy.deepcopy(topic_progress)
        original_evaluation_history = list(session.evaluation_history)
        
        try:
            # 2. Build EvaluationRecord
            record = EvaluationRecord(
                evaluation_id=evaluation.evaluation_id,
                question_record_id=evaluation.question_record_id,
                topic_id=evaluation.topic_id,
                overall_score=evaluation.overall_score,
                qualitative_coverage_signal=evaluation.qualitative_coverage_signal,
                follow_up_signal=evaluation.follow_up_signal,
                candidate_claim=evaluation.candidate_claim,
                interview_evidence=evaluation.interview_evidence,
                answer_text=evaluation.answer_text,
                timestamp=evaluation.evaluated_at
            )
            
            # Persist latest evidence state to topic_progress
            if evaluation.candidate_claim:
                topic_progress.candidate_claim = evaluation.candidate_claim
            if evaluation.interview_evidence:
                topic_progress.interview_evidence = evaluation.interview_evidence
            
            # 3. Update Aggregates
            agg = topic_progress.evaluation_aggregate
            agg.answers_evaluated += 1
            agg.cumulative_score += evaluation.overall_score
            agg.average_score = agg.cumulative_score / agg.answers_evaluated
            
            if evaluation.overall_score >= 0.8:
                agg.strong_answers += 1
            elif evaluation.overall_score >= 0.5:
                agg.partial_answers += 1
            elif evaluation.overall_score >= 0.3:
                agg.weak_answers += 1
            else:
                agg.insufficient_answers += 1
                
            topic_progress.coverage_score = agg.average_score
            topic_progress.readiness_score = agg.average_score
            
            # 4. Apply CoverageAssessment
            if coverage_assessment.is_covered:
                topic_progress.qualitatively_covered = True
                
            # Adaptive Difficulty
            from app.ai_interview.runtime.adaptive_difficulty_engine import AdaptiveDifficultyEngine
            AdaptiveDifficultyEngine.adapt(
                session=session,
                topic_progress=topic_progress,
                overall_score=evaluation.overall_score,
                strategy=session.strategy_snapshot,
                interview_evidence=evaluation.interview_evidence
            )
                
            # 5. Append to history
            session.evaluation_history.append(record)
            
        except Exception as e:
            # Rollback completely
            topic_progress.evaluation_aggregate = original_topic_progress.evaluation_aggregate
            topic_progress.coverage_score = original_topic_progress.coverage_score
            topic_progress.readiness_score = original_topic_progress.readiness_score
            topic_progress.qualitatively_covered = original_topic_progress.qualitatively_covered
            topic_progress.candidate_claim = original_topic_progress.candidate_claim
            topic_progress.interview_evidence = original_topic_progress.interview_evidence
            session.evaluation_history = original_evaluation_history
            raise EvaluationApplicationError(f"Failed to apply evaluation safely: {str(e)}")
