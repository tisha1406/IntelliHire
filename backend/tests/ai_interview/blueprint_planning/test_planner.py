import pytest
from app.ai_interview.blueprint_planning import (
    InterviewBlueprintPlanner,
    BlueprintPlanningRequest,
    JobRequirementContext,
    PlanningConstraints,
    ContextValidationError,
    BlueprintValidationError
)
from app.ai_interview.blueprint_planning.enums import TopicSourceCode
from app.ai_interview.resume_processing.schemas import CandidateInterviewContext, ExtractionMetadata
from app.ai_interview.resume_processing.enums import ExtractionQualityStatus
from app.ai_interview.schemas.resume import StructuredResume, Skill, Project
from app.ai_interview.schemas.interview_mode import InterviewModeDefinition, InterviewModeSettings
from app.ai_interview.core.enums import InterviewModeStatus, DifficultyLevel
from datetime import datetime

@pytest.fixture
def base_mode():
    return InterviewModeDefinition(
        mode_id="mode_base",
        name="Base Mode",
        description="...",
        version=1,
        status=InterviewModeStatus.PUBLISHED,
        settings=InterviewModeSettings(
            allowed_question_types=["initial", "follow_up"],
            difficulty_policy="medium"
        ),
        created_at=datetime.utcnow()
    )

@pytest.fixture
def empty_candidate():
    return CandidateInterviewContext(
        candidate_id="c1",
        structured_resume=StructuredResume(),
        extraction_metadata=ExtractionMetadata(
            source_type="pdf",
            extractor_name="test",
            extractor_version="1.0",
            character_count=1000,
            detected_sections=[],
            warning_count=0,
            processing_duration_ms=10
        ),
        quality_status=ExtractionQualityStatus.USABLE,
        warnings=[]
    )

def test_required_skill_absent_from_resume(empty_candidate, base_mode):
    # Job requires Python, resume has Java
    empty_candidate.structured_resume.skills.append(Skill(name="Java"))
    job_ctx = JobRequirementContext(
        role_title="Backend Engineer",
        required_skills=["Python"],
        interview_duration_minutes=30
    )
    req = BlueprintPlanningRequest(
        candidate_context=empty_candidate,
        mode_definition=base_mode,
        job_context=job_ctx
    )
    planner = InterviewBlueprintPlanner()
    blueprint = planner.plan(req)
    
    # Verify Python is included as ROLE_REQUIRED (mandatory)
    python_topic = next((t for t in blueprint.topics if t.topic_name == "Python"), None)
    assert python_topic is not None
    assert TopicSourceCode.ROLE_REQUIRED.value in python_topic.source
    assert python_topic.mandatory is True
    
    # Verify Java is included as RESUME_SKILL (optional)
    java_topic = next((t for t in blueprint.topics if t.topic_name == "Java"), None)
    assert java_topic is not None
    assert TopicSourceCode.RESUME_SKILL.value in java_topic.source
    assert java_topic.mandatory is False
    assert TopicSourceCode.ROLE_REQUIRED.value not in java_topic.source

def test_custom_mode_behavior(empty_candidate):
    # Mode requires behavioral
    custom_mode = InterviewModeDefinition(
        mode_id="mode_custom",
        name="Company X Custom",
        description="...",
        version=1,
        status=InterviewModeStatus.PUBLISHED,
        settings=InterviewModeSettings(
            allowed_question_types=["behavioral"],
            difficulty_policy="lenient"
        ),
        created_at=datetime.utcnow()
    )
    job_ctx = JobRequirementContext(
        role_title="Eng",
        interview_duration_minutes=30
    )
    req = BlueprintPlanningRequest(
        candidate_context=empty_candidate,
        mode_definition=custom_mode,
        job_context=job_ctx
    )
    planner = InterviewBlueprintPlanner()
    blueprint = planner.plan(req)
    
    behavioral = next((t for t in blueprint.topics if "Behavioral" in t.topic_name), None)
    assert behavioral is not None
    assert TopicSourceCode.MODE_REQUIRED.value in behavioral.source
    assert behavioral.initial_difficulty == DifficultyLevel.EASY
    assert behavioral.mandatory is True

def test_structured_explainability(empty_candidate, base_mode):
    # Both in resume and job requirements
    empty_candidate.structured_resume.skills.append(Skill(name="Go"))
    empty_candidate.structured_resume.projects.append(Project(name="Test", description="", technologies=["Go"]))
    job_ctx = JobRequirementContext(
        role_title="Go Dev",
        required_skills=["Go"],
        interview_duration_minutes=30
    )
    req = BlueprintPlanningRequest(
        candidate_context=empty_candidate,
        mode_definition=base_mode,
        job_context=job_ctx
    )
    planner = InterviewBlueprintPlanner()
    blueprint = planner.plan(req)
    
    go_topic = next(t for t in blueprint.topics if t.topic_name == "Go")
    # Explains all sources
    assert TopicSourceCode.ROLE_REQUIRED.value in go_topic.source
    assert TopicSourceCode.RESUME_SKILL.value in go_topic.source
    assert TopicSourceCode.PROJECT_EVIDENCE.value in go_topic.source
    
def test_impossible_budget(empty_candidate, base_mode):
    # Requires 5 mandatory skills, but duration is 5 minutes (max 1 budget)
    job_ctx = JobRequirementContext(
        role_title="Fullstack",
        required_skills=["A", "B", "C", "D", "E"],
        interview_duration_minutes=5 # Budget will be max(1, 5//5) = 1
    )
    req = BlueprintPlanningRequest(
        candidate_context=empty_candidate,
        mode_definition=base_mode,
        job_context=job_ctx,
        constraints=PlanningConstraints(total_question_budget=2) # Force budget to 2
    )
    planner = InterviewBlueprintPlanner()
    
    with pytest.raises(BlueprintValidationError, match="Impossible budget"):
        planner.plan(req)

def test_partially_usable_context(empty_candidate, base_mode):
    empty_candidate.quality_status = ExtractionQualityStatus.PARTIALLY_USABLE
    empty_candidate.structured_resume.skills.append(Skill(name="Python"))
    job_ctx = JobRequirementContext(
        role_title="Dev",
        interview_duration_minutes=30
    )
    req = BlueprintPlanningRequest(
        candidate_context=empty_candidate,
        mode_definition=base_mode,
        job_context=job_ctx
    )
    planner = InterviewBlueprintPlanner()
    # Should not raise exception
    blueprint = planner.plan(req)
    assert len(blueprint.topics) == 1

def test_unusable_context(empty_candidate, base_mode):
    empty_candidate.quality_status = ExtractionQualityStatus.UNUSABLE
    job_ctx = JobRequirementContext(
        role_title="Dev",
        interview_duration_minutes=30
    )
    req = BlueprintPlanningRequest(
        candidate_context=empty_candidate,
        mode_definition=base_mode,
        job_context=job_ctx
    )
    planner = InterviewBlueprintPlanner()
    with pytest.raises(ContextValidationError, match="UNUSABLE"):
        planner.plan(req)

def test_deterministic_reproducibility(empty_candidate, base_mode):
    # Setup candidate with diverse sources
    empty_candidate.structured_resume.skills.append(Skill(name="Docker"))
    empty_candidate.structured_resume.projects.append(Project(name="Cloud", description="", technologies=["Kubernetes", "AWS"]))
    
    job_ctx = JobRequirementContext(
        role_title="DevOps",
        required_skills=["AWS", "Docker"],
        interview_duration_minutes=45
    )
    req1 = BlueprintPlanningRequest(
        candidate_context=empty_candidate,
        mode_definition=base_mode,
        job_context=job_ctx
    )
    
    # Needs a deepcopy for a truly fresh request to avoid unintended mutability overlap,
    # but Pydantic's copy() / model_copy() works.
    req2 = BlueprintPlanningRequest(
        candidate_context=empty_candidate,
        mode_definition=base_mode,
        job_context=job_ctx
    )
    
    planner = InterviewBlueprintPlanner()
    blueprint1 = planner.plan(req1)
    blueprint2 = planner.plan(req2)
    
    # 1. Total Budgets
    assert blueprint1.total_question_budget == blueprint2.total_question_budget
    assert blueprint1.min_questions == blueprint2.min_questions
    assert blueprint1.max_questions == blueprint2.max_questions
    
    # 2. Topic Count
    assert len(blueprint1.topics) == len(blueprint2.topics)
    
    # 3. Exactly identical ordering, sources, priority, and difficulty
    for t1, t2 in zip(blueprint1.topics, blueprint2.topics):
        assert t1.topic_name == t2.topic_name
        assert t1.source == t2.source
        assert t1.priority == t2.priority
        assert t1.mandatory == t2.mandatory
        assert t1.initial_difficulty == t2.initial_difficulty
        # topic_id UUIDs will naturally differ, which is expected runtime behavior
        assert t1.topic_id != t2.topic_id
