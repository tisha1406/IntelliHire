from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from app.ai_interview.resume_processing.schemas import CandidateInterviewContext
from app.ai_interview.schemas.interview_mode import InterviewModeDefinition
from app.ai_interview.core.enums import InterviewType
from app.ai_interview.schemas.strategy import MixedComposition
from app.ai_interview.blueprint_planning.scenario_schemas import Scenario

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
    # D-03: needed so TopicSelector can deterministically decide whether a
    # situational topic must be produced (Situational/Case, or Mixed with
    # situational_case weight > 0). Previously the blueprint_planning
    # pipeline had no visibility into either field at all -- only
    # SessionInitializer received them, too late to influence topic
    # selection. The caller (session_creation_service.py) already derives
    # both from the campaign document; this just forwards them one step
    # earlier.
    interview_type: Optional[InterviewType] = None
    mixed_composition: Optional[MixedComposition] = None
    # The scenario already deterministically selected by ScenarioRepository
    # for this request's role/domain (or None if none is active). Fetching
    # happens in the async caller, not here -- TopicSelector/CoveragePlanner
    # stay synchronous and I/O-free, consistent with candidate_context and
    # job_context already being pre-fetched data rather than live repository
    # handles.
    selected_scenario: Optional[Scenario] = None
