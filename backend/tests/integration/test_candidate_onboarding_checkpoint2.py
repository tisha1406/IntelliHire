"""
MAIN WORKFLOW CHECKPOINT 2: Candidate Invitation -> Candidate Login ->
Candidate Dashboard -> Resume Upload -> Resume Processing -> Processed
Resume Available to Candidate.

Exercises the REAL candidate-portal services end to end (InvitationService,
AuthService, CandidatePortalService, ResumeProcessingService) against the
isolated test MongoDB (tests/conftest.py forces DATABASE_NAME=intellihire_test
for every pytest run) -- not the AI-interview resume-context pipeline
(app/ai_interview/resume_processing/), which is a separate area out of scope
for this checkpoint.

No real LLM call is made: GROQ_API_KEY is monkeypatched to empty, which
routes ResumeProcessingService through its own existing
"Warning: GROQ_API_KEY is missing. Using mock resume data." fallback branch
(resume_processing_service.py) -- not a new mock invented for this test.
"""
import fitz  # PyMuPDF
import pytest
import pytest_asyncio
from bson import ObjectId

from app.db.mongo import connect_db, close_db
from app.repositories.company_repository import CompanyRepository
from app.repositories.campaign_repository import CampaignRepository
from app.repositories.user_repository import UserRepository
from app.repositories.candidate_repository import CandidateRepository
from app.repositories.candidate_workflow_repository import CandidateWorkflowRepository
from app.repositories.resume_repository import ResumeRepository

from app.services.invitation_service import InvitationService
from app.services.auth_service import AuthService
from app.services.candidate_portal_service import CandidatePortalService
from app.services.resume_processing_service import ResumeProcessingService
from app.config.settings import settings


def _make_pdf_bytes(text: str) -> bytes:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text(fitz.Point(50, 50), text)
    return doc.write()


@pytest_asyncio.fixture
async def onboarding_fixtures():
    await connect_db()

    company_repo = CompanyRepository()
    campaign_repo = CampaignRepository()
    user_repo = UserRepository()
    candidate_repo = CandidateRepository()
    workflow_repo = CandidateWorkflowRepository()
    resume_repo = ResumeRepository()

    company_id = await company_repo.create({
        "general": {"name": "Checkpoint2 Test Co", "contact_email": "checkpoint2-company@example.com"},
        "status": "active",
    })
    campaign_id = await campaign_repo.create({
        "company_id": ObjectId(company_id),
        "name": "Checkpoint2 Backend Role",
        "job_position": "Backend Engineer",
        "status": "active",
    })

    created_ids = {"company_id": company_id, "campaign_id": campaign_id, "user_id": None, "candidate_id": None}

    yield created_ids

    # Cleanup -- isolated test DB, but still tidy up after ourselves.
    if created_ids.get("candidate_id"):
        await workflow_repo.collection.delete_many({"candidate_id": ObjectId(created_ids["candidate_id"])})
        await resume_repo.collection.delete_many({"candidate_id": ObjectId(created_ids["candidate_id"])})
        await candidate_repo.collection.delete_many({"_id": ObjectId(created_ids["candidate_id"])})
    if created_ids.get("user_id"):
        await user_repo.collection.delete_many({"_id": ObjectId(created_ids["user_id"])})
    await campaign_repo.collection.delete_many({"_id": ObjectId(campaign_id)})
    await company_repo.collection.delete_many({"_id": ObjectId(company_id)})

    await close_db()


@pytest.mark.asyncio
async def test_candidate_onboarding_checkpoint2_end_to_end(onboarding_fixtures, monkeypatch):
    ids = onboarding_fixtures

    # --- 1. Create/use an invited candidate (real InvitationService) -------
    invitation_service = InvitationService()
    invite_result = await invitation_service.invite_candidate(
        company_id=ids["company_id"],
        campaign_id=ids["campaign_id"],
        name="Checkpoint2 Candidate",
        email="checkpoint2-candidate@example.com",
    )
    ids["candidate_id"] = invite_result["candidate"]["id"]
    ids["user_id"] = (await UserRepository().get_by_email("checkpoint2-candidate@example.com"))["_id"].__str__()

    username = invite_result["credentials"]["username"]
    temp_password = invite_result["credentials"]["temporary_password"]
    assert username == "checkpoint2-candidate@example.com"

    # --- 2. Authenticate as Candidate using the invitation-issued creds ----
    auth_service = AuthService()
    login_result = await auth_service.login(email=username, password=temp_password)

    assert login_result["role"] == "candidate"
    assert login_result["candidate_context"]["candidate_id"] == ids["candidate_id"]
    assert login_result["candidate_context"]["company_id"] == ids["company_id"]

    candidate_id = login_result["candidate_context"]["candidate_id"]

    # --- 3. Load candidate dashboard ----------------------------------------
    portal_service = CandidatePortalService()
    dashboard = await portal_service.get_dashboard(candidate_id)

    assert dashboard.candidate_id == candidate_id
    assert dashboard.candidate_name == "Checkpoint2 Candidate"
    assert dashboard.company_id == ids["company_id"]
    assert dashboard.campaign_id == ids["campaign_id"]
    # An invited-but-not-yet-interviewed candidate must not be blocked by
    # missing practice/official-interview data.
    assert dashboard.next_action == "UPLOAD_RESUME"

    resume_status_before = await portal_service.get_resume_status(candidate_id)
    assert resume_status_before.has_resume is False

    # --- 4/5. Upload a small valid test resume + trigger real processing ---
    # (mock-data fallback branch, no real Groq call -- see module docstring)
    monkeypatch.setattr(settings, "GROQ_API_KEY", "")
    pdf_bytes = _make_pdf_bytes("Checkpoint2 Candidate\nBackend Engineer\nPython, FastAPI, MongoDB")

    processor = ResumeProcessingService()
    result = await processor.process_resume(
        candidate_id=candidate_id,
        company_id=ids["company_id"],
        campaign_id=ids["campaign_id"],
        file_bytes=pdf_bytes,
        filename="resume.pdf",
    )
    assert result is True

    # --- 6. Retrieve the candidate resume/analysis --------------------------
    resume_status_after = await portal_service.get_resume_status(candidate_id)
    assert resume_status_after.has_resume is True
    assert resume_status_after.status == "analysed"

    analysis = await portal_service.get_resume_analysis(candidate_id)
    assert analysis.overall_score > 0
    assert "Python" in analysis.technical_skills or len(analysis.technical_skills) > 0

    # Dashboard reflects the real (non-mocked) onboarding progress now.
    dashboard_after = await portal_service.get_dashboard(candidate_id)
    assert dashboard_after.next_action == "PRACTICE"

    # --- 7. The processed result belongs to the same candidate -------------
    raw_analysis_doc = await ResumeRepository().get_by_candidate(candidate_id)
    assert str(raw_analysis_doc["candidate_id"]) == candidate_id
    assert str(raw_analysis_doc["company_id"]) == ids["company_id"]
    assert str(raw_analysis_doc["campaign_id"]) == ids["campaign_id"]
