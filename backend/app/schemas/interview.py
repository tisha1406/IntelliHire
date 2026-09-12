from pydantic import BaseModel
from typing import Optional


class CreateSessionRequest(BaseModel):
    """
    Empty body for now. Campaign ID is in the path, token in the header.
    Any explicit overrides to the campaign settings could go here.
    """
    pass


class CreateSessionResponse(BaseModel):
    session_id: str
    state: str
    mode_id: str
    topics_count: int
    total_question_budget: int
    min_questions: int