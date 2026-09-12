from typing import List, Optional
from pydantic import BaseModel, Field
from app.ai_interview.core.enums import DifficultyLevel, QuestionType


class TopicBlueprint(BaseModel):
    topic_id: str
    topic_name: str
    source: str
    priority: int
    mandatory: bool = False
    initial_difficulty: DifficultyLevel = DifficultyLevel.MEDIUM
    allowed_question_types: List[QuestionType] = Field(default_factory=list)
    question_budget: int = Field(
        default=2,
        description="Number of questions allocated to this topic. Enforced by Phase 5 QuestionTurnPlanner."
    )


class InterviewBlueprint(BaseModel):
    blueprint_version: str
    total_question_budget: int
    min_questions: int
    max_questions: int
    emergency_max_questions: int
    topics: List[TopicBlueprint] = Field(default_factory=list)
