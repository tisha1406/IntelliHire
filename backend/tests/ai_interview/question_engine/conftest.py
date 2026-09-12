"""
Shared fixtures for Phase 5 question_engine tests.

All fixtures are deterministic. No external dependencies (no network, no LLM, no GPU).
"""
import pytest
from datetime import datetime

from app.ai_interview.core.enums import (
    InterviewState, DifficultyLevel, QuestionType, TopicState,
)
from app.ai_interview.runtime.enums import RuntimeAction
from app.ai_interview.runtime.schemas import RuntimeDecision
from app.ai_interview.schemas.blueprint import InterviewBlueprint, TopicBlueprint
from app.ai_interview.schemas.session import InterviewSessionSchema, TopicProgress
from app.ai_interview.schemas.interview_mode import (
    InterviewModeDefinition, InterviewModeSettings,
)
from app.ai_interview.core.enums import InterviewModeStatus
from app.ai_interview.resume_processing.schemas import (
    CandidateInterviewContext,
    ExtractionMetadata,
)
from app.ai_interview.resume_processing.enums import ExtractionQualityStatus
from app.ai_interview.schemas.resume import (
    StructuredResume, Skill, Project, Experience,
)
from app.ai_interview.question_engine.schemas import QuestionRecord


# ── Blueprint fixtures ─────────────────────────────────────────────────────────

@pytest.fixture
def python_topic() -> TopicBlueprint:
    return TopicBlueprint(
        topic_id="python",
        topic_name="Python",
        source="resume_skill",
        priority=5,
        mandatory=True,
        initial_difficulty=DifficultyLevel.MEDIUM,
        allowed_question_types=[QuestionType.INITIAL, QuestionType.SKILL_SPECIFIC],
        question_budget=3,
    )


@pytest.fixture
def sql_topic() -> TopicBlueprint:
    return TopicBlueprint(
        topic_id="sql",
        topic_name="SQL",
        source="resume_skill",
        priority=4,
        mandatory=False,
        initial_difficulty=DifficultyLevel.EASY,
        allowed_question_types=[QuestionType.INITIAL],
        question_budget=2,
    )


@pytest.fixture
def blueprint(python_topic, sql_topic) -> InterviewBlueprint:
    return InterviewBlueprint(
        blueprint_version="1.0",
        total_question_budget=5,
        min_questions=2,
        max_questions=5,
        emergency_max_questions=7,
        topics=[python_topic, sql_topic],
    )


# ── Session fixtures ───────────────────────────────────────────────────────────

@pytest.fixture
def session_in_progress(blueprint) -> InterviewSessionSchema:
    """Session that is IN_PROGRESS with current_topic_id=python."""
    return InterviewSessionSchema(
        session_id="test-session-001",
        candidate_id="cand-001",
        company_id="company-001",
        campaign_id="campaign-001",
        mode_id="mode-001",
        mode_version=1,
        state=InterviewState.IN_PROGRESS,
        blueprint=blueprint,
        questions_asked_total=0,
        current_topic_id="python",
        topic_progress=[
            TopicProgress(topic_id="python", state=TopicState.IN_PROGRESS, questions_asked=0),
            TopicProgress(topic_id="sql", state=TopicState.NOT_STARTED, questions_asked=0),
        ],
        created_at=datetime(2025, 1, 1, 10, 0, 0),
        started_at=datetime(2025, 1, 1, 10, 0, 1),
    )


@pytest.fixture
def runtime_decision_python() -> RuntimeDecision:
    """RuntimeDecision authorising progress on python topic."""
    return RuntimeDecision(
        current_state=InterviewState.IN_PROGRESS,
        allowed_action=RuntimeAction.NO_ACTION,
        active_topic_id="python",
        should_complete=False,
    )


# ── Mode fixture ───────────────────────────────────────────────────────────────

@pytest.fixture
def interview_mode() -> InterviewModeDefinition:
    return InterviewModeDefinition(
        mode_id="mode-001",
        name="Technical Interview",
        description="Standard technical interview mode",
        version=1,
        status=InterviewModeStatus.PUBLISHED,
        settings=InterviewModeSettings(
            allowed_question_types=["initial", "skill_specific"],
        ),
        created_at=datetime(2025, 1, 1),
    )


# ── Candidate context fixture ──────────────────────────────────────────────────

@pytest.fixture
def candidate_context() -> CandidateInterviewContext:
    return CandidateInterviewContext(
        candidate_id="cand-001",
        structured_resume=StructuredResume(
            professional_summary="Backend developer with 3 years Python experience.",
            skills=[
                Skill(name="Python", category="Programming Language", proficiency="Advanced"),
                Skill(name="SQL", category="Database", proficiency="Intermediate"),
                Skill(name="React", category="Frontend", proficiency="Beginner"),
            ],
            projects=[
                Project(
                    name="Flask API",
                    description="REST API built with Python and Flask",
                    technologies=["Python", "Flask", "PostgreSQL"],
                ),
                Project(
                    name="React Dashboard",
                    description="Frontend dashboard using React",
                    technologies=["React", "JavaScript"],
                ),
            ],
            experience=[
                Experience(
                    title="Python Backend Developer",
                    org="TechCorp",
                    description="Developed Python microservices and REST APIs",
                    duration="2 years",
                ),
            ],
        ),
        extraction_metadata=ExtractionMetadata(
            source_type="pdf",
            extractor_name="test",
            extractor_version="1.0",
            character_count=500,
            detected_sections=["skills", "projects", "experience"],
            warning_count=0,
            processing_duration_ms=50.0,
        ),
        quality_status=ExtractionQualityStatus.USABLE,
    )


# ── QuestionRecord helper ──────────────────────────────────────────────────────

def make_question_record(
    session_id: str = "test-session-001",
    turn_number: int = 1,
    topic_id: str = "python",
    question_text: str = "What is Python?",
    question_type: QuestionType = QuestionType.INITIAL,
    difficulty: DifficultyLevel = DifficultyLevel.MEDIUM,
) -> QuestionRecord:
    return QuestionRecord(
        session_id=session_id,
        turn_number=turn_number,
        topic_id=topic_id,
        question_text=question_text,
        question_type=question_type,
        difficulty=difficulty,
    )
