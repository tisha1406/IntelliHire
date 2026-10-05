from typing import List, Optional, Dict
from pydantic import BaseModel, Field, model_validator
from datetime import datetime, timezone

from app.ai_interview.core.enums import (
    InterviewType, QuestionCategory, DifficultyLevel
)

class TopicSelectionPolicy(BaseModel):
    policy_type: str = Field(default="priority_score", description="e.g. priority_score, round_robin, criticality_first")

class DifficultyPolicy(BaseModel):
    adapts: bool = True
    scope: str = Field(default="per_topic", description="per_topic or global")
    reset_on_switch: bool = True
    step_size: int = 1
    band_constrainable: bool = True

class FollowUpPolicy(BaseModel):
    allowed_categories: List[QuestionCategory] = Field(default_factory=list)
    max_per_topic: int = Field(default=2, ge=0)

class GapPolicy(BaseModel):
    enabled: bool = True
    max_share_of_budget: float = Field(default=0.4, ge=0.0, le=1.0)

class CompletionPolicy(BaseModel):
    allow_early_exit: bool = True
    require_all_critical_covered: bool = True

class CompanyOverrideBounds(BaseModel):
    target_questions_min_delta: int = 0
    target_questions_max_delta: int = 0
    allowed_difficulty_bands: List[DifficultyLevel] = Field(default_factory=list)

class StrategyDefinition(BaseModel):
    strategy_id: str
    name: str
    description: str
    version: int = 1
    is_active: bool = True

    applicable_interview_types: List[InterviewType] = Field(default_factory=list)

    budget_mode: str = Field(default="fixed", description="fixed or distinct_topics")

    min_questions: int = Field(ge=0)
    target_questions: int = Field(ge=0)
    max_questions: int = Field(ge=0)

    max_questions_per_topic: int = Field(ge=0)
    max_followups_per_topic: int = Field(ge=0)
    critical_topic_max_followups: Optional[int] = Field(default=None, ge=0)

    strong_threshold: float = Field(ge=0.0, le=1.0)
    acceptable_threshold: float = Field(ge=0.0, le=1.0)
    weak_threshold: float = Field(ge=0.0, le=1.0)

    topic_selection_policy: TopicSelectionPolicy = Field(default_factory=TopicSelectionPolicy)
    difficulty_policy: DifficultyPolicy = Field(default_factory=DifficultyPolicy)
    followup_policy: FollowUpPolicy = Field(default_factory=FollowUpPolicy)
    gap_policy: GapPolicy = Field(default_factory=GapPolicy)
    completion_policy: CompletionPolicy = Field(default_factory=CompletionPolicy)
    company_override_bounds: CompanyOverrideBounds = Field(default_factory=CompanyOverrideBounds)

    @model_validator(mode="after")
    def validate_strategy(self) -> "StrategyDefinition":
        # Check budgets
        if not (self.min_questions <= self.target_questions <= self.max_questions):
            raise ValueError("Budgets must satisfy: min_questions <= target_questions <= max_questions")
        
        # Check threshold ordering
        if not (self.weak_threshold <= self.acceptable_threshold <= self.strong_threshold):
            raise ValueError("Thresholds must satisfy: weak_threshold <= acceptable_threshold <= strong_threshold")

        return self

class CampaignStrategySnapshot(BaseModel):
    snapshot_id: str
    snapshotted_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    definition: StrategyDefinition

class MixedComposition(BaseModel):
    technical: float = Field(default=0.0, ge=0.0, le=1.0)
    resume_experience: float = Field(default=0.0, ge=0.0, le=1.0)
    hr_behavioral: float = Field(default=0.0, ge=0.0, le=1.0)
    situational_case: float = Field(default=0.0, ge=0.0, le=1.0)

    @model_validator(mode="after")
    def validate_composition(self) -> "MixedComposition":
        dimensions = [self.technical, self.resume_experience, self.hr_behavioral, self.situational_case]
        
        for weight in dimensions:
            if weight > 0 and weight < 0.10:
                raise ValueError("Selected dimensions must have a minimum weight of 0.10")
                
        total = sum(dimensions)
        if abs(total - 1.0) > 1e-5:
            raise ValueError("Mixed Composition weights must sum to exactly 1.0")
            
        return self

class RequirementCriticalityDef(BaseModel):
    skill: str
    criticality: str
