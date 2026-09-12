from typing import List, Optional
from pydantic import BaseModel, Field, model_validator


class AnswerEvaluation(BaseModel):
    correctness_score: float
    depth_score: float
    clarity_score: float
    confidence_score: float

    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    missing_concepts: List[str] = Field(default_factory=list)

    evaluation_summary: str

    @model_validator(mode="after")
    def validate_scores(self) -> "AnswerEvaluation":
        for score_name in ["correctness_score", "depth_score", "clarity_score", "confidence_score"]:
            score = getattr(self, score_name)
            if not (0.0 <= score <= 1.0):
                raise ValueError(f"{score_name} must be between 0.0 and 1.0")
        return self
