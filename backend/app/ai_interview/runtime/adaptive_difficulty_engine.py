from typing import Optional
from app.ai_interview.schemas.session import InterviewSessionSchema, TopicProgress
from app.ai_interview.schemas.strategy import StrategyDefinition, DifficultyPolicy
from app.ai_interview.core.enums import DifficultyLevel, TopicDimension, InterviewEvidence, BehavioralSpecificity

class AdaptiveDifficultyEngine:
    _ORDER = {
        DifficultyLevel.EASY: 1,
        DifficultyLevel.MEDIUM: 2,
        DifficultyLevel.HARD: 3
    }
    
    _LEVELS = {
        1: DifficultyLevel.EASY,
        2: DifficultyLevel.MEDIUM,
        3: DifficultyLevel.HARD
    }
    
    _BEHAVIORAL_ORDER = {
        BehavioralSpecificity.GENERAL: 1,
        BehavioralSpecificity.SPECIFIC: 2,
        BehavioralSpecificity.EVIDENCE_REQUIRED: 3
    }
    
    _BEHAVIORAL_LEVELS = {
        1: BehavioralSpecificity.GENERAL,
        2: BehavioralSpecificity.SPECIFIC,
        3: BehavioralSpecificity.EVIDENCE_REQUIRED
    }

    @classmethod
    def initialize_if_needed(
        cls, 
        session: InterviewSessionSchema, 
        topic_progress: TopicProgress,
        strategy: Optional[StrategyDefinition] = None
    ) -> None:
        """
        Initializes current_difficulty for a topic if it doesn't exist, 
        serving as the safe backward-compatible fallback for first-ever entry.
        Also initializes current_specificity if the dimension is behavioral.
        """
        if topic_progress.current_difficulty is None and topic_progress.dimension != TopicDimension.BEHAVIORAL:
            if strategy and strategy.difficulty_policy.scope == "global" and session.current_difficulty:
                topic_progress.current_difficulty = session.current_difficulty
            else:
                topic_progress.current_difficulty = cls._get_initial_difficulty(session, topic_progress.topic_id)
                
        if topic_progress.current_specificity is None and topic_progress.dimension == TopicDimension.BEHAVIORAL:
            topic_progress.current_specificity = BehavioralSpecificity.GENERAL

    @classmethod
    def handle_topic_switch(
        cls, 
        session: InterviewSessionSchema, 
        topic_progress: TopicProgress,
        previous_topic_id: Optional[str],
        strategy: Optional[StrategyDefinition] = None
    ) -> None:
        """
        Applies reset_on_switch logic when a topic switch is detected.
        Must be called precisely when session.current_topic_id changes.
        """
        if not strategy:
            cls.initialize_if_needed(session, topic_progress, strategy)
            return

        policy = strategy.difficulty_policy
        is_switch = previous_topic_id is not None and previous_topic_id != topic_progress.topic_id
        
        if is_switch:
            if policy.scope == "global":
                # In global scope, difficulty crosses topic boundaries.
                if policy.reset_on_switch:
                    # Rare but possible: start fresh on switch even if global
                    if topic_progress.dimension != TopicDimension.BEHAVIORAL:
                        topic_progress.current_difficulty = cls._get_initial_difficulty(session, topic_progress.topic_id)
                    else:
                        topic_progress.current_specificity = BehavioralSpecificity.GENERAL
                else:
                    # Inherit from the session's running global difficulty
                    if topic_progress.dimension != TopicDimension.BEHAVIORAL:
                        if session.current_difficulty:
                            topic_progress.current_difficulty = session.current_difficulty
                        else:
                            cls.initialize_if_needed(session, topic_progress, strategy)
                    else:
                        cls.initialize_if_needed(session, topic_progress, strategy)
            else:
                # Per-topic scope
                if policy.reset_on_switch:
                    if topic_progress.dimension != TopicDimension.BEHAVIORAL:
                        topic_progress.current_difficulty = cls._get_initial_difficulty(session, topic_progress.topic_id)
                    else:
                        topic_progress.current_specificity = BehavioralSpecificity.GENERAL
                else:
                    cls.initialize_if_needed(session, topic_progress, strategy)
        else:
            # Not a switch
            cls.initialize_if_needed(session, topic_progress, strategy)

    @classmethod
    def adapt(
        cls,
        session: InterviewSessionSchema,
        topic_progress: TopicProgress,
        overall_score: float,
        strategy: Optional[StrategyDefinition] = None,
        interview_evidence: Optional[InterviewEvidence] = None
    ) -> None:
        if not strategy:
            return
            
        policy = strategy.difficulty_policy
        
        if not policy.adapts:
            return
            
        # Ensure it's initialized before adapting
        cls.initialize_if_needed(session, topic_progress, strategy)
            
        if topic_progress.dimension == TopicDimension.BEHAVIORAL:
            cls._adapt_behavioral(topic_progress, interview_evidence)
            return

        current = topic_progress.current_difficulty
        current_idx = cls._ORDER.get(current, 2)
        
        # Evaluate performance against strategy thresholds
        # STRONG -> increase, WEAK -> decrease, ACCEPTABLE -> unchanged
        if overall_score >= strategy.strong_threshold:
            new_idx = current_idx + policy.step_size
        elif overall_score <= strategy.weak_threshold:
            new_idx = current_idx - policy.step_size
        else:
            new_idx = current_idx
            
        # Clamp to 1..3
        new_idx = max(1, min(3, new_idx))
        
        # Constrain by campaign bands if required
        if policy.band_constrainable and strategy.company_override_bounds and strategy.company_override_bounds.allowed_difficulty_bands:
            allowed_bands = strategy.company_override_bounds.allowed_difficulty_bands
            allowed_indices = [cls._ORDER.get(b, 2) for b in allowed_bands]
            min_allowed = min(allowed_indices)
            max_allowed = max(allowed_indices)
            
            new_idx = max(min_allowed, min(max_allowed, new_idx))
            
        new_difficulty = cls._LEVELS[new_idx]
        topic_progress.current_difficulty = new_difficulty
        
        # If global scope, sync the session's overall tracker
        if policy.scope == "global" and topic_progress.dimension != TopicDimension.BEHAVIORAL:
            session.current_difficulty = new_difficulty

    @classmethod
    def _adapt_behavioral(
        cls, 
        topic_progress: TopicProgress,
        interview_evidence: Optional[InterviewEvidence]
    ) -> None:
        if not interview_evidence:
            return
            
        current = topic_progress.current_specificity
        if not current:
            current = BehavioralSpecificity.GENERAL
            
        current_idx = cls._BEHAVIORAL_ORDER.get(current, 1)
        
        # Vague/general answer -> increase specificity requirement
        if interview_evidence == InterviewEvidence.NOT_DEMONSTRATED:
            new_idx = current_idx + 1
        # Some specific detail, but lacks evidence -> move toward evidence-oriented
        elif interview_evidence == InterviewEvidence.BASIC:
            new_idx = current_idx + 1
        # Already strong/acceptable -> don't unnecessarily force deeper
        else:
            new_idx = current_idx
            
        new_idx = max(1, min(3, new_idx))
        topic_progress.current_specificity = cls._BEHAVIORAL_LEVELS[new_idx]

    @classmethod
    def _get_initial_difficulty(cls, session: InterviewSessionSchema, topic_id: str) -> DifficultyLevel:
        topic_bp = next((t for t in session.blueprint.topics if t.topic_id == topic_id), None)
        return topic_bp.initial_difficulty if topic_bp else DifficultyLevel.MEDIUM
