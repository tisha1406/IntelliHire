from typing import Dict, List, Optional
import logging
from app.ai_interview.schemas.session import InterviewSessionSchema, TopicProgress
from app.ai_interview.core.enums import (
    RequirementCriticality, ResumeEvidence, TopicDimension, InterviewType
)

logger = logging.getLogger(__name__)

class TopicPriorityResult:
    def __init__(
        self,
        topic_id: str,
        priority: float,
        criticality_multiplier: float,
        dimension: Optional[TopicDimension],
        resume_evidence_score: float,
        coverage_score: float,
        inverse_confidence: float,
        composition_score: float,
        breakdown: Dict[str, float]
    ):
        self.topic_id = topic_id
        self.priority = priority
        self.criticality_multiplier = criticality_multiplier
        self.dimension = dimension
        self.resume_evidence_score = resume_evidence_score
        self.coverage_score = coverage_score
        self.inverse_confidence = inverse_confidence
        self.composition_score = composition_score
        self.breakdown = breakdown

class ShadowPriorityCalculator:
    """
    Deterministic shadow priority scoring for official interview architectures.
    Limitations: Currently uses `readiness_score` as a proxy for inverse confidence, 
    which might not perfectly isolate purely LLM-reported confidence if readiness includes other factors.
    """
    
    @staticmethod
    def calculate_priority(
        session: InterviewSessionSchema,
        topic: TopicProgress,
        w_resume: float = 1.0,
        w_composition: float = 1.0,
        w_performance: float = 1.0,
        w_coverage: float = 1.0
    ) -> TopicPriorityResult:
        
        # 1. Criticality Multiplier
        crit_map = {
            RequirementCriticality.CRITICAL: 1.5,
            RequirementCriticality.REQUIRED: 1.2,
            RequirementCriticality.PREFERRED: 1.0,
            RequirementCriticality.RESUME_ONLY: 0.7
        }
        # If no criticality is set, default to PREFERRED (1.0)
        criticality = topic.criticality or RequirementCriticality.PREFERRED
        crit_multiplier = crit_map.get(criticality, 1.0)
        
        # 2. Resume Evidence
        resume_map = {
            ResumeEvidence.ABSENT: 0.0,
            ResumeEvidence.PARTIAL: 0.5,
            ResumeEvidence.STRONG: 1.0
        }
        resume_score = resume_map.get(topic.resume_evidence, 0.0) if topic.resume_evidence else 0.0
        
        # 3. Composition Score
        composition_score = 0.0
        
        # Ensure fallback safety for old campaigns that lack interview_type or mixed_composition
        i_type = getattr(session, "interview_type", None)
        mixed_comp = getattr(session, "mixed_composition", None)
        
        if i_type == InterviewType.MIXED and mixed_comp and topic.dimension:
            dimension_value = topic.dimension.value
            if dimension_value == TopicDimension.TECHNICAL.value:
                composition_score = mixed_comp.technical or 0.0
            elif dimension_value == TopicDimension.RESUME.value:
                composition_score = mixed_comp.resume_experience or 0.0
            elif dimension_value == TopicDimension.BEHAVIORAL.value:
                composition_score = mixed_comp.hr_behavioral or 0.0
            elif dimension_value == TopicDimension.SITUATIONAL.value:
                composition_score = mixed_comp.situational_case or 0.0
        
        # 4. Performance / Inverse Confidence
        # Uses readiness_score (0.0 to 1.0) as a proxy for confidence.
        # Strong evidence (readiness ~ 1.0) -> low inverse confidence (0.0)
        # Weak evidence (readiness ~ 0.0) -> high inverse confidence (1.0)
        inverse_confidence = 1.0 - topic.readiness_score
        
        # 5. Coverage Score
        coverage = topic.coverage_score
        coverage_term = 1.0 - coverage
        
        # Combine
        base_priority = (
            w_resume * resume_score +
            w_composition * composition_score +
            w_performance * inverse_confidence +
            w_coverage * coverage_term
        )
        
        priority = round(crit_multiplier * base_priority, 4)
        
        breakdown = {
            "w_resume_term": w_resume * resume_score,
            "w_composition_term": w_composition * composition_score,
            "w_performance_term": w_performance * inverse_confidence,
            "w_coverage_term": w_coverage * coverage_term,
            "base_priority": base_priority
        }
        
        return TopicPriorityResult(
            topic_id=topic.topic_id,
            priority=priority,
            criticality_multiplier=crit_multiplier,
            dimension=topic.dimension,
            resume_evidence_score=resume_score,
            coverage_score=coverage,
            inverse_confidence=inverse_confidence,
            composition_score=composition_score,
            breakdown=breakdown
        )

    @classmethod
    def get_best_topic(cls, session: InterviewSessionSchema, unresolved_topics: List[TopicProgress]) -> Optional[TopicPriorityResult]:
        if not unresolved_topics:
            return None
            
        results = [cls.calculate_priority(session, t) for t in unresolved_topics]
        
        def min_key(r: TopicPriorityResult):
            # Sort order:
            # 1. higher priority -> smaller -priority
            # 2. higher criticality -> smaller -criticality_multiplier
            # 3. lower coverage -> smaller coverage_score
            # 4. stable lexical topic_id -> smaller topic_id (string comparison)
            return (
                -r.priority,
                -r.criticality_multiplier,
                r.coverage_score,
                r.topic_id
            )
            
        results.sort(key=min_key)
        return results[0]
