// Enum values mirrored exactly from backend/app/ai_interview/core/enums.py.
// These are authoring-form option lists only — no interview decision logic lives here.

export const INTERVIEW_TYPES = [
    { value: "technical", label: "Technical" },
    { value: "resume_experience", label: "Resume / Experience" },
    { value: "hr_behavioral", label: "HR / Behavioral" },
    { value: "situational_case", label: "Situational / Case" },
    { value: "mixed", label: "Mixed" },
];

export const QUESTION_CATEGORIES = [
    { value: "new", label: "New" },
    { value: "gap_verification", label: "Gap Verification" },
    { value: "followup_clarification", label: "Follow-up: Clarification" },
    { value: "followup_depth", label: "Follow-up: Depth" },
    { value: "followup_evidence", label: "Follow-up: Evidence" },
    { value: "followup_challenge", label: "Follow-up: Technical Challenge" },
    { value: "correction", label: "Correction" },
];

export const DIFFICULTY_LEVELS = [
    { value: "easy", label: "Easy" },
    { value: "medium", label: "Medium" },
    { value: "hard", label: "Hard" },
];

export const TOPIC_SELECTION_POLICY_TYPES = [
    { value: "priority_score", label: "Priority Score" },
    { value: "round_robin", label: "Round Robin" },
    { value: "criticality_first", label: "Criticality First" },
];

export const DIFFICULTY_SCOPES = [
    { value: "per_topic", label: "Per Topic" },
    { value: "global", label: "Global" },
];

export const BUDGET_MODES = [
    { value: "fixed", label: "Fixed" },
    { value: "distinct_topics", label: "Distinct Topics" },
];
