"""
MAIN WORKFLOW CHECKPOINT 5 regression tests: dashboard -> report navigation.

Root cause fixed: DashboardResponse never carried the candidate's own
completed official interview session_id. Reports.jsx requires a session_id
query parameter to show anything (otherwise it renders a "please select a
session" empty state); session_id is never persisted onto the candidate or
workflow document anywhere else. Dashboard.jsx's "View Report" action
(next_action == "VIEW_REPORT", set by Checkpoint 4's complete_interview())
linked to a bare "/candidate/reports" with no session_id, so a candidate
returning to the dashboard after finishing their interview (rather than
clicking through immediately from the InterviewComplete screen, which
already builds the link correctly) had no way to actually open their report
from the dashboard.

Fix: CandidatePortalService.get_dashboard() resolves the candidate's most
recent COMPLETED, non-practice interview_sessions document (only once
official_completed is True, to avoid an extra query otherwise) and exposes
it as DashboardResponse.official_session_id. No change to
InterviewResultService, ReportResponse, or any PDF code.

Exercises the real CandidatePortalService against the isolated test MongoDB
(tests/conftest.py forces DATABASE_NAME=intellihire_test), inserting minimal
interview_sessions documents directly (not re-running the full AI interview
engine, which is unmodified and already covered by other tests).
"""
from datetime import datetime, timezone

from bson import ObjectId
import pytest
import pytest_asyncio

from app.db.mongo import connect_db, close_db, get_database
from app.repositories.company_repository import CompanyRepository
from app.repositories.campaign_repository import CampaignRepository
from app.repositories.user_repository import UserRepository
from app.repositories.candidate_repository import CandidateRepository
from app.repositories.candidate_workflow_repository import CandidateWorkflowRepository

from app.services.invitation_service import InvitationService
from app.services.candidate_portal_service import CandidatePortalService


@pytest_asyncio.fixture
async def checkpoint5_fixtures():
    await connect_db()

    company_repo = CompanyRepository()
    campaign_repo = CampaignRepository()
    user_repo = UserRepository()
    candidate_repo = CandidateRepository()
    workflow_repo = CandidateWorkflowRepository()
    db = get_database()

    company_id = await company_repo.create({
        "general": {"name": "Checkpoint5 Test Co", "contact_email": "checkpoint5-company@example.com"},
        "status": "active",
    })
    campaign_id = await campaign_repo.create({
        "company_id": ObjectId(company_id),
        "name": "Checkpoint5 Backend Role",
        "job_position": "Backend Engineer",
        "status": "active",
    })

    invitation_service = InvitationService()
    invite_result = await invitation_service.invite_candidate(
        company_id=company_id,
        campaign_id=campaign_id,
        name="Checkpoint5 Candidate",
        email="checkpoint5-candidate@example.com",
    )
    candidate_id = invite_result["candidate"]["id"]
    user_id = (await user_repo.get_by_email("checkpoint5-candidate@example.com"))["_id"]

    yield {"company_id": company_id, "campaign_id": campaign_id, "candidate_id": candidate_id}

    await db.interview_sessions.delete_many({"candidate_id": candidate_id})
    await workflow_repo.collection.delete_many({"candidate_id": ObjectId(candidate_id)})
    await candidate_repo.collection.delete_many({"_id": ObjectId(candidate_id)})
    await user_repo.collection.delete_many({"_id": ObjectId(user_id)})
    await campaign_repo.collection.delete_many({"_id": ObjectId(campaign_id)})
    await company_repo.collection.delete_many({"_id": ObjectId(company_id)})

    await close_db()


def _session_doc(candidate_id, session_id, mode_id, state, completed_at=None):
    return {
        "session_id": session_id,
        "candidate_id": candidate_id,
        "mode_id": mode_id,
        "state": state,
        "completed_at": completed_at,
    }


@pytest.mark.asyncio
async def test_official_session_id_is_none_before_completion(checkpoint5_fixtures):
    candidate_id = checkpoint5_fixtures["candidate_id"]
    service = CandidatePortalService()

    dashboard = await service.get_dashboard(candidate_id)

    assert dashboard.official_session_id is None


@pytest.mark.asyncio
async def test_official_session_id_populated_after_official_completion(checkpoint5_fixtures):
    candidate_id = checkpoint5_fixtures["candidate_id"]
    db = get_database()
    service = CandidatePortalService()

    await db.interview_sessions.insert_one(_session_doc(
        candidate_id, "sess-official-1", "technical", "completed",
        completed_at=datetime.now(timezone.utc),
    ))
    await service.complete_interview(candidate_id)

    dashboard = await service.get_dashboard(candidate_id)

    assert dashboard.official_session_id == "sess-official-1"


@pytest.mark.asyncio
async def test_official_session_id_excludes_practice_sessions(checkpoint5_fixtures):
    """A completed practice session must never be surfaced as the
    candidate's report session -- Practice/Official isolation."""
    candidate_id = checkpoint5_fixtures["candidate_id"]
    db = get_database()
    service = CandidatePortalService()

    await db.interview_sessions.insert_one(_session_doc(
        candidate_id, "sess-practice-1", "practice", "completed",
        completed_at=datetime.now(timezone.utc),
    ))
    await service.complete_interview(candidate_id)

    dashboard = await service.get_dashboard(candidate_id)

    assert dashboard.official_session_id is None
    assert dashboard.official_session_id != "sess-practice-1"


@pytest.mark.asyncio
async def test_official_session_id_picks_the_most_recent_completed_session(checkpoint5_fixtures):
    candidate_id = checkpoint5_fixtures["candidate_id"]
    db = get_database()
    service = CandidatePortalService()

    await db.interview_sessions.insert_one(_session_doc(
        candidate_id, "sess-official-old", "technical", "completed",
        completed_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
    ))
    await db.interview_sessions.insert_one(_session_doc(
        candidate_id, "sess-official-new", "technical", "completed",
        completed_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    ))
    await service.complete_interview(candidate_id)

    dashboard = await service.get_dashboard(candidate_id)

    assert dashboard.official_session_id == "sess-official-new"


@pytest.mark.asyncio
async def test_in_progress_official_session_not_surfaced_as_reportable(checkpoint5_fixtures):
    """An official session that is still IN_PROGRESS must not be surfaced as
    the report session (no report exists for it yet)."""
    candidate_id = checkpoint5_fixtures["candidate_id"]
    db = get_database()
    service = CandidatePortalService()

    await db.interview_sessions.insert_one(_session_doc(
        candidate_id, "sess-in-progress", "technical", "in_progress",
    ))

    dashboard = await service.get_dashboard(candidate_id)

    assert dashboard.official_session_id is None
