# backend/app/ai_interview/question_engine/prompts/registry.py

from dataclasses import dataclass
from typing import List, Optional

@dataclass
class CombinationConfig:
    combination_id: str
    strategy_id: str
    interview_type: str
    dimension_source: str # "interview_type" or "topic"
    allowed_categories: List[str]

# The EXACT 16 combinations according to the Claude Prompt Library.
COMBINATION_REGISTRY = [
    # Adaptive Depth
    CombinationConfig("AD_TECH", "adaptive_depth", "technical", "interview_type", ["new", "followup_clarification", "followup_depth", "followup_evidence", "followup_challenge", "correction", "gap_verification"]),
    CombinationConfig("AD_MIXED", "adaptive_depth", "mixed", "topic", ["new", "followup_clarification", "followup_depth", "followup_evidence", "followup_challenge", "correction", "gap_verification"]),

    # Fixed Coverage
    CombinationConfig("FC_TECH", "fixed_coverage", "technical", "interview_type", ["new", "followup_clarification", "followup_depth", "followup_evidence", "correction"]),
    CombinationConfig("FC_RESUME", "fixed_coverage", "resume_experience", "interview_type", ["new", "followup_clarification", "followup_depth", "followup_evidence", "correction"]),
    CombinationConfig("FC_BEHAV", "fixed_coverage", "hr_behavioral", "interview_type", ["new", "followup_clarification", "followup_depth", "followup_evidence", "correction"]),
    CombinationConfig("FC_SIT", "fixed_coverage", "situational_case", "interview_type", ["new", "followup_clarification", "followup_depth", "followup_evidence", "correction"]),
    CombinationConfig("FC_MIXED", "fixed_coverage", "mixed", "topic", ["new", "followup_clarification", "followup_depth", "followup_evidence", "correction"]),

    # Critical Skills Deep Dive
    CombinationConfig("CS_TECH", "critical_skills", "technical", "interview_type", ["new", "followup_clarification", "followup_depth", "followup_evidence", "followup_challenge", "correction"]),

    # Breadth Screening
    CombinationConfig("BS_TECH", "breadth", "technical", "interview_type", ["new", "followup_clarification"]),
    CombinationConfig("BS_RESUME", "breadth", "resume_experience", "interview_type", ["new", "followup_clarification"]),
    CombinationConfig("BS_BEHAV", "breadth", "hr_behavioral", "interview_type", ["new", "followup_clarification"]),
    CombinationConfig("BS_SIT", "breadth", "situational_case", "interview_type", ["new", "followup_clarification"]),
    CombinationConfig("BS_MIXED", "breadth", "mixed", "topic", ["new", "followup_clarification"]),

    # Requirement Gap Verification
    CombinationConfig("GV_TECH", "gap_verification", "technical", "interview_type", ["gap_verification", "new", "followup_clarification", "followup_depth", "followup_evidence"]),
    CombinationConfig("GV_MIXED", "gap_verification", "mixed", "topic", ["gap_verification", "new", "followup_clarification", "followup_depth", "followup_evidence"]),

    # Behavioral Adaptive
    CombinationConfig("BA_HR", "behavioral_adaptive", "hr_behavioral", "interview_type", ["new", "followup_clarification", "followup_depth", "followup_evidence"])
]

def get_combination(strategy_id: str, interview_type: str) -> Optional[CombinationConfig]:
    for config in COMBINATION_REGISTRY:
        if config.strategy_id == strategy_id and config.interview_type == interview_type:
            return config
    return None

def map_interview_type_to_dimension(interview_type: str) -> str:
    """Maps the core InterviewType to the Prompt Library dimension naming."""
    mapping = {
        "technical": "technical",
        "resume_experience": "resume",
        "hr_behavioral": "behavioral",
        "situational_case": "situational"
    }
    return mapping.get(interview_type, interview_type)
