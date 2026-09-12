from enum import Enum


class InterviewModeStatus(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"


class InterviewState(str, Enum):
    CREATED = "created"
    INITIALIZING = "initializing"
    PLANNING = "planning"
    IN_PROGRESS = "in_progress"
    ASKING = "asking"
    LISTENING = "listening"
    PROCESSING = "processing"
    EVALUATING = "evaluating"
    DECIDING = "deciding"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


class TopicState(str, Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COVERED = "covered"
    FAILED_ABANDONED = "failed_abandoned"


class DifficultyLevel(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class QuestionType(str, Enum):
    INITIAL = "initial"
    FOLLOW_UP = "follow_up"
    CLARIFICATION = "clarification"
    BEHAVIORAL = "behavioral"
    PROJECT_SPECIFIC = "project_specific"
    SKILL_SPECIFIC = "skill_specific"


class InterviewDecision(str, Enum):
    NEXT_TOPIC = "next_topic"
    FOLLOW_UP = "follow_up"
    CLARIFICATION = "clarification"
    COMPLETE = "complete"


class MatchLabel(str, Enum):
    STRONG_MATCH = "strong_match"
    POTENTIAL_MATCH = "potential_match"
    NEEDS_REVIEW = "needs_review"


class DecisionReasonCode(str, Enum):
    LOW_READINESS = "low_readiness"
    LOW_TOPIC_COVERAGE = "low_topic_coverage"
    FOLLOW_UP_ALLOWED = "follow_up_allowed"
    FOLLOW_UP_LIMIT_REACHED = "follow_up_limit_reached"
    QUESTION_BUDGET_REACHED = "question_budget_reached"
    MINIMUM_QUESTIONS_NOT_MET = "minimum_questions_not_met"
    MANDATORY_TOPICS_PENDING = "mandatory_topics_pending"
    MANDATORY_TOPICS_ATTEMPTED = "mandatory_topics_attempted"
    EMERGENCY_MAX_REACHED = "emergency_max_reached"
    CONFIDENCE_THRESHOLD_MET = "confidence_threshold_met"
