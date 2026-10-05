from typing import Optional
from pydantic import BaseModel
from app.ai_interview.core.enums import DifficultyLevel


class Scenario(BaseModel):
    """
    A single situational/case scenario from the scenario bank (D-03).

    role_or_domain is the normalized (lowercase, trimmed) matching key
    ScenarioRepository filters on -- see ScenarioRepository.get_active_for_role.
    """
    scenario_id: str
    role_or_domain: str
    topic_name: str
    scenario_context: str
    difficulty: DifficultyLevel = DifficultyLevel.MEDIUM
    is_active: bool = True
