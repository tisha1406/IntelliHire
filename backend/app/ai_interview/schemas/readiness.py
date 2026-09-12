from typing import Dict, Any, Optional
from pydantic import BaseModel, Field, model_validator


class ReadinessResult(BaseModel):
    score: float
    confidence: float
    components: Dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_scores(self) -> "ReadinessResult":
        for score_name in ["score", "confidence"]:
            val = getattr(self, score_name)
            if not (0.0 <= val <= 1.0):
                raise ValueError(f"{score_name} must be between 0.0 and 1.0")
        return self
