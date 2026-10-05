"""
G-03 regression: real AuthService.login() end to end, against the isolated
test MongoDB (tests/conftest.py forces DATABASE_NAME=intellihire_test).

specs.md (Section 20) confirmed: "JWT payload never includes name/email
claims, but AuthContext.jsx:59-61,182-184 reads decoded.name/decoded.email --
these are permanently empty strings for every user, everywhere in the app
that relies on the auth context ... for display name/email."

Each role resolves name/email from a different place at login time (company:
general.name/general.contact_email on the company doc itself; candidate: the
candidate profile's name plus the user doc's email; recruiter/admin: the
user doc's own name/email) -- one test per role proves the real value reaches
the issued JWT, not a placeholder.
"""
from datetime import UTC, datetime

from bson import ObjectId
from jose import jwt
import pytest
import pytest_asyncio

from app.auth.jwt_handler import hash_password
from app.config.settings import settings
from app.db.mongo import connect_db, close_db
from app.repositories.company_repository import CompanyRepository
from app.repositories.campaign_repository import CampaignRepository
from app.repositories.user_repository import UserRepository
from app.repositories.candidate_repository import CandidateRepository
from app.services.auth_service import AuthService
from app.services.invitation_service import InvitationService


def _claims(access_token: str) -> dict:
    return jwt.decode(access_token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])


@pytest_asyncio.fixture
async def identity_fixtures():
    await connect_db()

    company_repo = CompanyRepository()
    campaign_repo = CampaignRepository()
    user_repo = UserRepository()
    candidate_repo = CandidateRepository()
    ids = {}

    company_id = await company_repo.create({
        "general": {"name": "G03 Verify Co", "contact_email": "g03-company@example.com"},
        "credentials": {"password_hash": hash_password("CompanyPass123!")},
        "status": "active",
    })
    ids["company"] = company_id

    campaign_id = await campaign_repo.create({
        "company_id": ObjectId(company_id), "name": "G03 Role", "job_position": "Engineer", "status": "active",
    })
    ids["campaign"] = campaign_id

    recruiter_id = await user_repo.create({
        "name": "Alex Recruiter", "email": "g03-recruiter@example.com",
        "password_hash": hash_password("RecruiterPass123!"),
        "role": "recruiter", "company_id": ObjectId(company_id),
        "is_active": True, "must_change_password": False,
        "recruiter_id": str(ObjectId()),
    })
    ids["recruiter"] = recruiter_id

    admin_id = await user_repo.create({
        "name": "System Administrator", "email": "g03-admin@example.com",
        "password_hash": hash_password("AdminPass123!"),
        "role": "admin", "is_active": True,
    })
    ids["admin"] = admin_id

    invite = await InvitationService().invite_candidate(
        company_id=company_id, campaign_id=campaign_id,
        name="Priya Candidate", email="g03-candidate@example.com",
    )
    candidate_id = invite["candidate"]["id"]
    candidate_user = await user_repo.get_by_email("g03-candidate@example.com")
    candidate_user_id = str(candidate_user["_id"])
    ids["candidate"] = candidate_id
    ids["candidate_user"] = candidate_user_id

    # InvitationService generates its own temp password; set a known one.
    await user_repo.update(candidate_user_id, {"password_hash": hash_password("CandidatePass123!")})

    yield {
        "company": {"email": "g03-company@example.com", "password": "CompanyPass123!", "expected_name": "G03 Verify Co"},
        "recruiter": {"email": "g03-recruiter@example.com", "password": "RecruiterPass123!", "expected_name": "Alex Recruiter"},
        "admin": {"email": "g03-admin@example.com", "password": "AdminPass123!", "expected_name": "System Administrator"},
        "candidate": {"email": "g03-candidate@example.com", "password": "CandidatePass123!", "expected_name": "Priya Candidate"},
    }

    from app.db.mongo import get_database
    db = get_database()
    await db.candidate_workflows.delete_many({"candidate_id": ObjectId(candidate_id)})
    await candidate_repo.collection.delete_many({"_id": ObjectId(candidate_id)})
    await user_repo.collection.delete_many({"_id": {"$in": [ObjectId(recruiter_id), ObjectId(admin_id), ObjectId(candidate_user_id)]}})
    await campaign_repo.collection.delete_many({"_id": ObjectId(campaign_id)})
    await company_repo.collection.delete_many({"_id": ObjectId(company_id)})

    await close_db()


@pytest.mark.asyncio
async def test_company_login_issues_real_company_name_and_email(identity_fixtures):
    creds = identity_fixtures["company"]

    result = await AuthService().login(creds["email"], creds["password"])

    claims = _claims(result["access_token"])
    assert claims["name"] == creds["expected_name"]
    assert claims["email"] == creds["email"]


@pytest.mark.asyncio
async def test_recruiter_login_issues_real_recruiter_name_and_email(identity_fixtures):
    creds = identity_fixtures["recruiter"]

    result = await AuthService().login(creds["email"], creds["password"])

    claims = _claims(result["access_token"])
    assert claims["name"] == creds["expected_name"]
    assert claims["email"] == creds["email"]


@pytest.mark.asyncio
async def test_admin_login_issues_real_admin_name_and_email(identity_fixtures):
    creds = identity_fixtures["admin"]

    result = await AuthService().login(creds["email"], creds["password"])

    claims = _claims(result["access_token"])
    assert claims["name"] == creds["expected_name"]
    assert claims["email"] == creds["email"]


@pytest.mark.asyncio
async def test_candidate_login_issues_the_candidate_profile_name_and_user_email(identity_fixtures):
    """The candidate's `users` doc has no `name` field at all (see
    InvitationService) -- the display name has to come from the candidate
    profile doc instead. This is the case specs.md's bug made permanently
    blank even though the real name was one lookup away the whole time."""
    creds = identity_fixtures["candidate"]

    result = await AuthService().login(creds["email"], creds["password"])

    claims = _claims(result["access_token"])
    assert claims["name"] == creds["expected_name"]
    assert claims["email"] == creds["email"]
