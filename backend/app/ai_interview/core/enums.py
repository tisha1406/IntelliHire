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


class BehavioralSpecificity(str, Enum):
    GENERAL = "general"
    SPECIFIC = "specific"
    EVIDENCE_REQUIRED = "evidence_required"


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


class InterviewType(str, Enum):
    TECHNICAL = "technical"
    RESUME_EXPERIENCE = "resume_experience"
    HR_BEHAVIORAL = "hr_behavioral"
    SITUATIONAL_CASE = "situational_case"
    MIXED = "mixed"


class TopicDimension(str, Enum):
    TECHNICAL = "technical"
    RESUME = "resume"
    BEHAVIORAL = "behavioral"
    SITUATIONAL = "situational"


class RequirementCriticality(str, Enum):
    CRITICAL = "critical"
    REQUIRED = "required"
    PREFERRED = "preferred"
    RESUME_ONLY = "resume_only"


class ResumeEvidence(str, Enum):
    ABSENT = "absent"
    PARTIAL = "partial"
    STRONG = "strong"


class InterviewEvidence(str, Enum):
    NOT_DEMONSTRATED = "not_demonstrated"
    BASIC = "basic"
    ACCEPTABLE = "acceptable"
    STRONG = "strong"


class QuestionCategory(str, Enum):
    NEW = "new"
    GAP_VERIFICATION = "gap_verification"
    FOLLOWUP_CLARIFICATION = "followup_clarification"
    FOLLOWUP_DEPTH = "followup_depth"
    FOLLOWUP_EVIDENCE = "followup_evidence"
    FOLLOWUP_CHALLENGE = "followup_challenge"
    CORRECTION = "correction"


class TopicSource(str, Enum):
    RESUME = "resume"
    REQUIREMENT = "requirement"
    GAP = "gap"
    BEHAVIORAL = "behavioral"


class TopicTerminalReason(str, Enum):
    MAX_QUESTIONS_REACHED = "max_questions_reached"
    SUFFICIENT_COVERAGE = "sufficient_coverage"
    BUDGET_EXHAUSTED = "budget_exhausted"
    DEPRIORITIZED = "deprioritized"


class CompletionReason(str, Enum):
    MAX_QUESTIONS_REACHED = "max_questions_reached"
    SUFFICIENT_COVERAGE = "sufficient_coverage"
    TOPICS_EXHAUSTED = "topics_exhausted"
    BUDGET_EXHAUSTED = "budget_exhausted"
    MANDATORY_TOPICS_ATTEMPTED = "mandatory_topics_attempted"
    MANDATORY_TOPICS_PENDING = "mandatory_topics_pending"
