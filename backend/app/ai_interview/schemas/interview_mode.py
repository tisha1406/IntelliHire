from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from app.ai_interview.core.enums import InterviewModeStatus


class InterviewModeSettings(BaseModel):
    allowed_question_types: list[str] = Field(default_factory=list)
    difficulty_policy: Optional[str] = None
    follow_up_policy: Optional[str] = None
    question_budget_policy: Optional[str] = None
    threshold_configuration: Dict[str, float] = Field(default_factory=dict)
    question_style: Optional[str] = None


class InterviewModeDefinition(BaseModel):
    mode_id: str
    name: str
    description: str
    version: int
    status: InterviewModeStatus
    settings: InterviewModeSettings = Field(default_factory=InterviewModeSettings)
    created_at: datetime
    created_by: Optional[str] = None
    published_at: Optional[datetime] = None
