from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, model_validator
from datetime import datetime


class ValidationResult(BaseModel):
    passed: bool
    hard_failures: List[str] = Field(default_factory=list)
    soft_warnings: List[str] = Field(default_factory=list)
    scores: Dict[str, float] = Field(default_factory=dict)
    retry_number: int = 0

    @model_validator(mode="after")
    def validate_rules(self) -> "ValidationResult":
        if self.hard_failures and self.passed:
            raise ValueError("Validation cannot pass if there are hard failures")
        return self
