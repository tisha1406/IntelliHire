from enum import Enum

class TopicSourceCode(str, Enum):
    ROLE_REQUIRED = "ROLE_REQUIRED"
    RESUME_SKILL = "RESUME_SKILL"
    PROJECT_EVIDENCE = "PROJECT_EVIDENCE"
    EXPERIENCE_EVIDENCE = "EXPERIENCE_EVIDENCE"
    MODE_REQUIRED = "MODE_REQUIRED"
    # D-03: a topic sourced from the deterministic situational scenario bank
    # (ScenarioRepository), used for Situational/Case interviews and the
    # situational slice of Mixed interviews. No other existing source code
    # represents this -- see session_initializer.py's dimension bridge for
    # why this is required (nothing else maps to TopicDimension.SITUATIONAL).
    SITUATIONAL_SCENARIO = "SITUATIONAL_SCENARIO"
