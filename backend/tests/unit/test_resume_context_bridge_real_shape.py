"""
Regression tests: ResumeContextBridge against the REAL persisted resume shape.

Root cause: ResumeProcessingService persists the candidate-portal resume as a
ResumeStructuredOutput document (technical_skills, experience[].company,
projects[] with name/description only, ...), but ResumeContextBridge only
read the engine/legacy keys "skills" and "org". Every real candidate's
CandidateInterviewContext therefore had no skills and blank organisations,
so SessionInitializer marked every topic ResumeEvidence.ABSENT.

The fixture below is validated against ResumeStructuredOutput itself so it
cannot silently drift from the production contract. The pre-existing
test_resume_context_bridge.py (legacy "extracted_data"/"skills"/"org"
shape) is intentionally untouched and must keep passing.
"""
from datetime import datetime, timezone

from bson import ObjectId

from app.services.resume_processing_service import ResumeStructuredOutput
from app.ai_interview.transport.services.resume_context_bridge import ResumeContextBridge
from app.ai_interview.blueprint_planning.schemas import BlueprintPlanningRequest, JobRequirementContext
from app.ai_interview.blueprint_planning.topic_selector import TopicSelector
from app.ai_interview.blueprint_planning.priority_allocator import PriorityAllocator
from app.ai_interview.blueprint_planning.difficulty_planner import DifficultyPlanner
from app.ai_interview.blueprint_planning.coverage_planner import CoveragePlanner
from app.ai_interview.runtime.session_initializer import SessionInitializer
from app.ai_interview.schemas.interview_mode import InterviewModeDefinition, InterviewModeSettings
from app.ai_interview.core.enums import InterviewModeStatus, ResumeEvidence, InterviewType


def _persisted_resume_doc(**overrides):
    structured = {
        "overall_score": 80, "ats_score": 80, "role_match": 80, "completeness": 80,
        "technical_skills": ["Python", "React"],
        "soft_skills": ["Communication"],
        "experience": [
            {"title": "Backend Engineer", "company": "Acme Corp", "duration": "2021-2024",
             "description": "Built Python microservices."},
        ],
        "education": [{"degree": "B.S. Computer Science", "institution": "State University", "year": "2019"}],
        "projects": [{"name": "Inventory App", "description": "Stock tracking web app."}],
        "missing_skills": [], "certifications": ["AWS Certified Developer"],
        "languages_known": ["English"],
        "radar_data": [{"subject": "Backend", "A": 80, "fullMark": 100}],
        "strengths": [], "weaknesses": [], "improve_ats": "", "missing_keywords": [],
        "grammar_score": 90, "formatting_score": 90,
    }
    structured.update(overrides)
    ResumeStructuredOutput.model_validate(structured)  # anchors the fixture to production
    # What ResumeProcessingService.process_resume() additionally persists:
    structured.update({
        "candidate_id": ObjectId(), "company_id": ObjectId(), "campaign_id": ObjectId(),
        "timeline": [{"title": "Resume Uploaded", "status": "done"}],
        "updated_at": datetime.now(timezone.utc),
    })
    return structured


def _build(**overrides):
    return ResumeContextBridge.build(_persisted_resume_doc(**overrides), "cand-1").structured_resume


class TestRealPersistedShape:
    def test_technical_skills_become_context_skills(self):
        resume = _build()
        assert [s.name for s in resume.skills] == ["Python", "React"]

    def test_soft_skills_are_not_mapped_into_skills(self):
        resume = _build()
        assert "Communication" not in [s.name for s in resume.skills]

    def test_experience_company_becomes_org_and_other_fields_preserved(self):
        exp = _build().experience[0]
        assert exp.org == "Acme Corp"
        assert exp.title == "Backend Engineer"
        assert exp.duration == "2021-2024"
        assert exp.description == "Built Python microservices."

    def test_projects_map_using_the_fields_actually_persisted(self):
        project = _build().projects[0]
        assert project.name == "Inventory App"
        assert project.description == "Stock tracking web app."

    def test_no_fabricated_project_technologies_or_summary(self):
        resume = _build()
        assert resume.projects[0].technologies == []   # not persisted -> not invented
        assert resume.professional_summary is None     # not persisted -> not invented

    def test_education_and_certifications_preserved(self):
        resume = _build()
        assert resume.education[0].degree == "B.S. Computer Science"
        assert resume.education[0].institution == "State University"
        assert resume.education[0].year == "2019"
        assert [c.name for c in resume.certifications] == ["AWS Certified Developer"]

    def test_empty_and_missing_optional_fields_are_safe(self):
        doc = _persisted_resume_doc(technical_skills=[], experience=[], projects=[], certifications=[])
        for key in ("technical_skills", "experience", "projects", "education", "certifications"):
            doc.pop(key, None)
        resume = ResumeContextBridge.build(doc, "cand-1").structured_resume
        assert resume.skills == [] and resume.experience == [] and resume.projects == []

    def test_candidate_scoping_is_preserved(self):
        ctx = ResumeContextBridge.build(_persisted_resume_doc(), "cand-xyz")
        assert ctx.candidate_id == "cand-xyz"

    def test_legacy_engine_shape_still_maps(self):
        """Backward compatibility with the engine/legacy keys the bridge
        previously (and still) accepts."""
        doc = {"extracted_data": {
            "skills": ["Go"], "experience": [{"title": "Dev", "org": "Legacy Inc"}],
        }}
        resume = ResumeContextBridge.build(doc, "c").structured_resume
        assert [s.name for s in resume.skills] == ["Go"]
        assert resume.experience[0].org == "Legacy Inc"


class TestDownstreamEvidence:
    """persisted resume -> bridge -> real planner -> SessionInitializer."""

    def _session(self, required_skills, doc):
        ctx = ResumeContextBridge.build(doc, "cand-1")
        mode = InterviewModeDefinition(
            mode_id="technical", name="T", description="d", version=1,
            status=InterviewModeStatus.PUBLISHED,
            settings=InterviewModeSettings(allowed_question_types=["initial"]),
            created_at=datetime.now(timezone.utc),
        )
        job = JobRequirementContext(role_title="Backend Engineer", required_skills=required_skills,
                                    interview_duration_minutes=30)
        request = BlueprintPlanningRequest(candidate_context=ctx, mode_definition=mode, job_context=job,
                                           interview_type=InterviewType.TECHNICAL)
        topics = TopicSelector.select_topics(request)
        PriorityAllocator.allocate(topics)
        blueprint = CoveragePlanner.plan(request, topics, DifficultyPlanner.determine_initial_difficulty(request))
        session = SessionInitializer.initialize(
            blueprint=blueprint, candidate_id="cand-1", company_id="co", campaign_id="ca",
            mode_id="technical", mode_version=1,
            campaign_requirements=[{"skill": s, "criticality": "required"} for s in required_skills],
            candidate_context=ctx,
        )
        names = {t.topic_id: t.topic_name for t in blueprint.topics}
        return {names[tp.topic_id]: tp for tp in session.topic_progress}, blueprint

    def test_resume_skill_present_is_strong_not_absent(self):
        progress, _ = self._session(["Python", "Kubernetes"], _persisted_resume_doc())
        assert progress["Python"].resume_evidence == ResumeEvidence.STRONG
        assert progress["Kubernetes"].resume_evidence == ResumeEvidence.ABSENT

    def test_resume_skills_now_produce_resume_skill_topics(self):
        _, blueprint = self._session([], _persisted_resume_doc())
        by_name = {t.topic_name: t.source for t in blueprint.topics}
        assert "RESUME_SKILL" in by_name["Python"]
        assert "RESUME_SKILL" in by_name["React"]
