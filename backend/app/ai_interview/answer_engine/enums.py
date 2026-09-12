from enum import Enum

class EvaluationSignal(str, Enum):
    STRONG = "strong"
    PARTIAL = "partial"
    WEAK = "weak"
    INSUFFICIENT = "insufficient"

class CoverageSignal(str, Enum):
    NOT_COVERED = "not_covered"
    PARTIALLY_COVERED = "partially_covered"
    QUALITATIVELY_COVERED = "qualitatively_covered"

class AnswerValidity(str, Enum):
    VALID = "valid"
    EMPTY = "empty"
    TOO_SHORT = "too_short"
    INVALID = "invalid"

class FollowUpSignal(str, Enum):
    NONE = "none"
    CLARIFICATION_MAY_HELP = "clarification_may_help"
    DEPTH_PROBE_MAY_HELP = "depth_probe_may_help"

class AnswerStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    EVALUATED = "evaluated"
    FAILED = "failed"
