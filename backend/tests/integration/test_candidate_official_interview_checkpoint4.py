"""
MAIN WORKFLOW CHECKPOINT 4 regression tests: Official Interview completion
persistence, and Practice/Official workflow-state isolation.

Root cause fixed: CandidatePortalService had no method that ever set
candidate_workflows.official_completed=True (it was only ever initialized to
False at invite time -- see invitation_service.py). The dashboard's Official
Interview step therefore could never show "completed", even after a
candidate actually finished the real interview. This mirrors the exact same
bug class as the already-fixed Practice completion issue
(complete_practice()), and the fix mirrors complete_practice() exactly:
CandidatePortalService.complete_interview() + POST
/api/candidate/interview/complete.

These tests exercise the real CandidatePortalService against the isolated
test MongoDB (tests/conftest.py forces DATABASE_NAME=intellihire_test) --
no AI-interview-engine code is touched or needed, since this is purely a
candidate-workflow persistence concern.
"""
from bson import ObjectId
import pytest
import pytest_asyncio

from app.db.mongo import connect_db, close_db
from app.repositories.company_repository import CompanyRepository
from app.repositories.campaign_repository import CampaignRepository
from app.repositories.user_repository import UserRepository
from app.repositories.candidate_repository import CandidateRepository
from app.repositories.candidate_workflow_repository import CandidateWorkflowRepository

from app.services.invitation_service import InvitationService
from app.services.candidate_portal_service import CandidatePortalService


@pytest_asyncio.fixture
async def checkpoint4_fixtures():
    await connect_db()

    company_repo = CompanyRepository()
    campaign_repo = CampaignRepository()
    user_repo = UserRepository()
    candidate_repo = CandidateRepository()
    workflow_repo = CandidateWorkflowRepository()

    company_id = await company_repo.create({
        "general": {"name": "Checkpoint4 Test Co", "contact_email": "checkpoint4-company@example.com"},
        "status": "active",
    })
    campaign_id = await campaign_repo.create({
        "company_id": ObjectId(company_id),
        "name": "Checkpoint4 Backend Role",
        "job_position": "Backend Engineer",
        "status": "active",
    })

    invitation_service = InvitationService()
    invite_result = await invitation_service.invite_candidate(
        company_id=company_id,
        campaign_id=campaign_id,
        name="Checkpoint4 Candidate",
        email="checkpoint4-candidate@example.com",
    )
    candidate_id = invite_result["candidate"]["id"]
    user_id = (await user_repo.get_by_email("checkpoint4-candidate@example.com"))["_id"]

    yield {"company_id": company_id, "campaign_id": campaign_id, "candidate_id": candidate_id}

    await workflow_repo.collection.delete_many({"candidate_id": ObjectId(candidate_id)})
    await candidate_repo.collection.delete_many({"_id": ObjectId(candidate_id)})
    await user_repo.collection.delete_many({"_id": ObjectId(user_id)})
    await campaign_repo.collection.delete_many({"_id": ObjectId(campaign_id)})
    await company_repo.collection.delete_many({"_id": ObjectId(company_id)})

    await close_db()


@pytest.mark.asyncio
async def test_complete_interview_persists_official_completed(checkpoint4_fixtures):
    candidate_id = checkpoint4_fixtures["candidate_id"]
    service = CandidatePortalService()
    workflow_repo = CandidateWorkflowRepository()

    before = await workflow_repo.get_by_candidate(candidate_id)
    assert before.get("official_completed", False) is False

    await service.complete_interview(candidate_id)

    after = await workflow_repo.get_by_candidate(candidate_id)
    assert after["official_completed"] is True
    assert after.get("official_completed_at") is not None
    assert after["next_action"] == "VIEW_REPORT"


@pytest.mark.asyncio
async def test_complete_interview_reflected_on_dashboard(checkpoint4_fixtures):
    candidate_id = checkpoint4_fixtures["candidate_id"]
    service = CandidatePortalService()

    await service.complete_interview(candidate_id)
    dashboard = await service.get_dashboard(candidate_id)

    official_step = next(s for s in dashboard.steps if s.key == "official")
    assert official_step.status == "completed"
    assert official_step.completed_at is not None


@pytest.mark.asyncio
async def test_complete_interview_does_not_modify_practice_state(checkpoint4_fixtures):
    """Official completion must not accidentally change practice_completed
    or any other practice-related workflow field."""
    candidate_id = checkpoint4_fixtures["candidate_id"]
    service = CandidatePortalService()
    workflow_repo = CandidateWorkflowRepository()

    await service.complete_practice(candidate_id)
    before = await workflow_repo.get_by_candidate(candidate_id)
    assert before["practice_completed"] is True

    await service.complete_interview(candidate_id)

    after = await workflow_repo.get_by_candidate(candidate_id)
    assert after["practice_completed"] is True  # unchanged
    assert after.get("practice_completed_at") == before.get("practice_completed_at")
    assert after["official_completed"] is True


@pytest.mark.asyncio
async def test_complete_practice_does_not_modify_official_state(checkpoint4_fixtures):
    """Symmetric isolation check: practice completion must not touch
    official_completed/official_started."""
    candidate_id = checkpoint4_fixtures["candidate_id"]
    service = CandidatePortalService()
    workflow_repo = CandidateWorkflowRepository()

    await service.start_interview(candidate_id)
    before = await workflow_repo.get_by_candidate(candidate_id)
    assert before["official_started"] is True
    assert before.get("official_completed", False) is False

    await service.complete_practice(candidate_id)

    after = await workflow_repo.get_by_candidate(candidate_id)
    assert after["official_started"] is True  # unchanged
    assert after.get("official_completed", False) is False  # unchanged
    assert after["practice_completed"] is True
