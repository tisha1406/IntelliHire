from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from app.ai_interview.resume_processing.schemas import CandidateInterviewContext
from app.ai_interview.schemas.interview_mode import InterviewModeDefinition

class JobRequirementContext(BaseModel):
    role_title: str
    department: Optional[str] = None
    required_skills: List[str] = Field(default_factory=list)
    preferred_skills: List[str] = Field(default_factory=list)
    job_description: Optional[str] = None
    experience_expectations: Optional[str] = None
    interview_duration_minutes: int = 30

class PlanningConstraints(BaseModel):
    max_topics: Optional[int] = None
    total_question_budget: Optional[int] = None

class BlueprintPlanningRequest(BaseModel):
    candidate_context: CandidateInterviewContext
    mode_definition: InterviewModeDefinition
    job_context: JobRequirementContext
    constraints: Optional[PlanningConstraints] = None
