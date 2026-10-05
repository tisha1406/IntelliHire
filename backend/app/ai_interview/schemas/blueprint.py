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
    # D-03: immutable snapshot of the scenario selected for this topic (only
    # set when source includes SITUATIONAL_SCENARIO). Snapshotted here rather
    # than referencing the live scenario document so an edit/deactivation of
    # the scenario bank after session creation can never change an
    # in-progress interview. D-04 will read scenario_context from here to
    # populate QuestionTurnPlan.scenario_context (question_turn_planner.py);
    # that wiring is explicitly out of scope for D-03.
    scenario_id: Optional[str] = None
    scenario_context: Optional[str] = None


class InterviewBlueprint(BaseModel):
    blueprint_version: str
    total_question_budget: int
    min_questions: int
    max_questions: int
    emergency_max_questions: int
    topics: List[TopicBlueprint] = Field(default_factory=list)
