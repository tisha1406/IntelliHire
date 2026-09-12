from typing import Optional, List
from pydantic import BaseModel, Field
from app.ai_interview.core.enums import InterviewState, DecisionReasonCode
from app.ai_interview.runtime.enums import RuntimeAction
from app.ai_interview.schemas.decision_trace import CompletionDecisionTrace

class TransitionResult(BaseModel):
    success: bool
    action: RuntimeAction
    previous_state: Optional[InterviewState] = None
    new_state: Optional[InterviewState] = None
    error: Optional[str] = None

class RuntimeDecision(BaseModel):
    current_state: InterviewState
    allowed_action: RuntimeAction
    active_topic_id: Optional[str] = None
    should_complete: bool = False
    completion_trace: Optional[CompletionDecisionTrace] = None
    reason_codes: List[DecisionReasonCode] = Field(default_factory=list)
