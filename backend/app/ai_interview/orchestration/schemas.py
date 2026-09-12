from typing import Optional
from pydantic import BaseModel
from app.ai_interview.runtime.enums import RuntimeAction
from app.ai_interview.question_engine.schemas import QuestionRecord
from app.ai_interview.answer_engine.schemas import EvaluationRecord

class InterviewTurnResult(BaseModel):
    action: RuntimeAction
    question: Optional[QuestionRecord] = None
    evaluation: Optional[EvaluationRecord] = None
    interview_completed: bool = False
    waiting_for_answer: bool = False
    current_topic_id: Optional[str] = None
