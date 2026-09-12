"""
Phase 5 — Question Orchestration & Interview Turn Engine

Configuration constants. Centralised to avoid magic numbers in business logic.
"""


class QuestionEngineConfig:
    # Maximum number of generation+validation attempts before giving up.
    MAX_GENERATION_ATTEMPTS: int = 3

    # Structural constraints on the generated question text.
    MIN_QUESTION_LENGTH: int = 10
    MAX_QUESTION_LENGTH: int = 500

    # Maximum number of previously-asked questions sent as context to the generator.
    # This keeps the generation request bounded and deterministic.
    MAX_PREVIOUS_QUESTIONS_CONTEXT: int = 10
