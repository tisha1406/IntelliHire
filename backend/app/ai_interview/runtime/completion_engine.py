from typing import Tuple
from app.ai_interview.schemas.session import InterviewSessionSchema
from app.ai_interview.core.enums import DecisionReasonCode, InterviewDecision, TopicState
from app.ai_interview.schemas.decision_trace import CompletionDecisionTrace

class CompletionEngine:
    @staticmethod
    def evaluate(session: InterviewSessionSchema) -> Tuple[bool, CompletionDecisionTrace]:
        """
        Determines if completion is allowed/forced based on deterministic counters.
        Phase 4 reads counters but NEVER increments them itself.
        """
        bp = session.blueprint
        
        # Check mandatory topics
        mandatory_topic_ids = {t.topic_id for t in bp.topics if t.mandatory}
        
        unresolved_mandatory = []
        abandoned_mandatory = []
        covered_mandatory = []
        
        for prog in session.topic_progress:
            if prog.topic_id in mandatory_topic_ids:
                if prog.state == TopicState.COVERED:
                    covered_mandatory.append(prog)
                elif prog.state == TopicState.FAILED_ABANDONED:
                    abandoned_mandatory.append(prog)
                else:
                    unresolved_mandatory.append(prog)

        mandatory_attempted = len(unresolved_mandatory) == 0
        
        # Reasons
        reason_codes = []
        should_complete = False
        
        if len(unresolved_mandatory) > 0:
            reason_codes.append(DecisionReasonCode.MANDATORY_TOPICS_PENDING)
        else:
            reason_codes.append(DecisionReasonCode.MANDATORY_TOPICS_ATTEMPTED)
            if len(abandoned_mandatory) == 0:
                # All mandatory topics cleanly covered
                should_complete = True
                reason_codes.append(DecisionReasonCode.CONFIDENCE_THRESHOLD_MET) # Placeholder reason for all done
            else:
                # Attempted all, but some were abandoned. Not completely successful coverage.
                should_complete = True
                reason_codes.append(DecisionReasonCode.LOW_TOPIC_COVERAGE)
                
        # Budget Check
        budget_exhausted = False
        if session.questions_asked_total >= bp.total_question_budget:
            budget_exhausted = True
            should_complete = True
            reason_codes.append(DecisionReasonCode.QUESTION_BUDGET_REACHED)
            
        trace = CompletionDecisionTrace(
            questions_asked_total=session.questions_asked_total,
            min_questions=bp.min_questions,
            max_questions=bp.max_questions,
            emergency_max_questions=bp.emergency_max_questions,
            mandatory_topics_attempted=mandatory_attempted,
            overall_confidence=0.0,  # Phase 4 has no evaluation
            threshold=0.0,
            decision=InterviewDecision.COMPLETE if should_complete else InterviewDecision.NEXT_TOPIC,
            reason_codes=reason_codes
        )
        
        return should_complete, trace
