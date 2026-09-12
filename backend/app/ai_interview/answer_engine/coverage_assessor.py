from app.ai_interview.schemas.session import TopicEvaluationAggregate, TopicProgress
from app.ai_interview.answer_engine.schemas import EvaluationResult
from app.ai_interview.answer_engine.enums import CoverageSignal
from app.ai_interview.answer_engine.config import MIN_QUESTIONS_FOR_COVERAGE

class CoverageAssessment:
    def __init__(self, is_covered: bool):
        self.is_covered = is_covered

class CoverageAssessor:
    """
    Evaluates aggregate deterministic evidence to decide if a topic is fully covered.
    Prevents a single weak/strong answer from bypassing topic budgets.
    """
    
    @staticmethod
    def assess(
        aggregate_pre_evaluation: TopicEvaluationAggregate,
        evaluation: EvaluationResult,
        topic_progress: TopicProgress,
        topic_budget: int
    ) -> CoverageAssessment:
        
        # Update hypothetical aggregate with the new evaluation
        new_answers_evaluated = aggregate_pre_evaluation.answers_evaluated + 1
        new_cumulative = aggregate_pre_evaluation.cumulative_score + evaluation.overall_score
        new_avg = new_cumulative / new_answers_evaluated
        
        strong_count = aggregate_pre_evaluation.strong_answers
        if evaluation.overall_score >= 0.8:
            strong_count += 1
            
        # Minimum questions logic
        # Cannot cover a topic if we haven't met the global minimum questions requirement
        if topic_progress.questions_asked < MIN_QUESTIONS_FOR_COVERAGE:
            return CoverageAssessment(is_covered=False)
            
        # Deterministic Coverage Logic
        # Condition A: Topic budget exhausted
        if topic_progress.questions_asked >= topic_budget:
            # If average is decent, it's qualitatively covered, otherwise failed_abandoned in Phase 4.
            if new_avg >= 0.5:
                return CoverageAssessment(is_covered=True)
            else:
                return CoverageAssessment(is_covered=False)
                
        # Condition B: Strong ongoing evidence before budget is exhausted
        if evaluation.qualitative_coverage_signal == CoverageSignal.QUALITATIVELY_COVERED:
            # Protect from a single LLM hallucination
            if topic_budget <= 1:
                return CoverageAssessment(is_covered=True)
            elif strong_count >= 2:
                return CoverageAssessment(is_covered=True)
                
        return CoverageAssessment(is_covered=False)
