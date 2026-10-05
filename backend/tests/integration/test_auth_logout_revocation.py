"""
G-02 regression: real end-to-end logout/revocation flow against the real
FastAPI app and the isolated test MongoDB (tests/conftest.py forces
DATABASE_NAME=intellihire_test).

specs.md Section 20 confirmed the prior state: logout was "server-side
no-op (comment: 'Clear refresh token from DB logic can go here')" -- the
endpoint always returned success without touching the stored refresh token
at all, so a refresh token obtained before logout kept working afterwards.

These tests drive the real /api/auth/login, /api/auth/logout and
/api/auth/refresh endpoints (not mocks) and prove:
  * logout revokes the authenticated account's own stored refresh token,
  * the revoked token can no longer be used via /api/auth/refresh,
  * logout never revokes a *different* account's refresh token,
  * this holds for every account type that can log in (candidate, recruiter,
    admin, company),
  * logout's response/status is unchanged,
  * a refresh token belonging to an account that has NOT logged out still
    works (G-01's flow is not broken by this change).

Fixture setup uses a plain synchronous pymongo.MongoClient (same pattern as
tests/integration/test_auth_refresh_flow.py / test_auth_smoke.py), not the
async repositories: the TestClient's app lifespan opens its own motor client
bound to its own event loop, and an async fixture on pytest-asyncio's
separate loop cannot share it.
"""
from bson import ObjectId
from fastapi.testclient import TestClient
from pymongo import MongoClient
import pytest

from app.auth.jwt_handler import hash_password
from app.config.settings import settings
from app.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def logout_fixtures(client):
    sync_client = MongoClient(settings.MONGO_URI)
    db = sync_client[settings.DATABASE_NAME]

    emails = [
        "g02-recruiter-a@example.com", "g02-recruiter-b@example.com",
        "g02-admin@example.com", "g02-candidate@example.com",
    ]
    db.companies.delete_many({"general.contact_email": "g02-company@example.com"})
    db.users.delete_many({"email": {"$in": emails}})
    db.candidates.delete_many({"email": "g02-candidate@example.com"})
    db.campaigns.delete_many({"name": "G02 Role"})

    company_id = db.companies.insert_one({
        "general": {"name": "G02 Verify Co", "contact_email": "g02-company@example.com"},
        "credentials": {"password_hash": hash_password("CompanyPass123!")},
        "status": "active",
    }).inserted_id

    campaign_id = db.campaigns.insert_one({
        "company_id": company_id, "name": "G02 Role", "job_position": "Engineer", "status": "active",
    }).inserted_id

    # Two independent recruiters -- used for the cross-account isolation check.
    recruiter_a_id = db.users.insert_one({
        "name": "G02 Recruiter A", "email": "g02-recruiter-a@example.com",
        "password_hash": hash_password("RecruiterPass123!"),
        "role": "recruiter", "company_id": company_id,
        "is_active": True, "must_change_password": False, "recruiter_id": str(ObjectId()),
    }).inserted_id

    recruiter_b_id = db.users.insert_one({
        "name": "G02 Recruiter B", "email": "g02-recruiter-b@example.com",
        "password_hash": hash_password("RecruiterPass123!"),
        "role": "recruiter", "company_id": company_id,
        "is_active": True, "must_change_password": False, "recruiter_id": str(ObjectId()),
    }).inserted_id

    admin_id = db.users.insert_one({
        "name": "G02 Admin", "email": "g02-admin@example.com",
        "password_hash": hash_password("AdminPass123!"),
        "role": "admin", "is_active": True,
    }).inserted_id

    candidate_user_id = db.users.insert_one({
        "email": "g02-candidate@example.com",
        "password_hash": hash_password("CandidatePass123!"),
        "role": "candidate", "company_id": company_id,
        "is_active": True, "must_change_password": False,
    }).inserted_id

    candidate_id = db.candidates.insert_one({
        "user_id": candidate_user_id, "company_id": company_id, "campaign_id": campaign_id,
        "name": "G02 Candidate", "email": "g02-candidate@example.com",
        "target_role": "Engineer", "status": "active",
    }).inserted_id
    db.users.update_one({"_id": candidate_user_id}, {"$set": {"candidate_id": candidate_id}})

    yield {
        "db": db,
        "company": {"email": "g02-company@example.com", "password": "CompanyPass123!"},
        "recruiter_a": {"email": "g02-recruiter-a@example.com", "password": "RecruiterPass123!"},
        "recruiter_b": {"email": "g02-recruiter-b@example.com", "password": "RecruiterPass123!"},
        "admin": {"email": "g02-admin@example.com", "password": "AdminPass123!"},
        "candidate": {"email": "g02-candidate@example.com", "password": "CandidatePass123!"},
    }

    db.candidates.delete_many({"_id": candidate_id})
    db.users.delete_many({"_id": {"$in": [recruiter_a_id, recruiter_b_id, admin_id, candidate_user_id]}})
    db.campaigns.delete_many({"_id": campaign_id})
    db.companies.delete_many({"_id": company_id})
    sync_client.close()


def _login(client, creds):
    resp = client.post("/api/auth/login", json=creds)
    assert resp.status_code == 200, resp.text
    return resp.json()["data"]


def _logout(client, access_token):
    return client.post("/api/auth/logout", headers={"Authorization": f"Bearer {access_token}"})


def _refresh(client, refresh_token):
    return client.post("/api/auth/refresh", json={"refresh_token": refresh_token})


class TestLogoutRevokesTheOwnRefreshToken:
    @pytest.mark.parametrize("account_key", ["recruiter_a", "admin", "candidate", "company"])
    def test_logout_then_refresh_is_rejected(self, client, logout_fixtures, account_key):
        login_data = _login(client, logout_fixtures[account_key])

        logout_resp = _logout(client, login_data["access_token"])
        assert logout_resp.status_code == 200

        refresh_resp = _refresh(client, login_data["refresh_token"])

        assert refresh_resp.status_code == 401

    def test_logout_response_is_unchanged(self, client, logout_fixtures):
        login_data = _login(client, logout_fixtures["recruiter_a"])

        resp = _logout(client, login_data["access_token"])

        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert body["message"] == "Logged out successfully"
        assert body["data"] is None


class TestLogoutDoesNotAffectOtherAccounts:
    def test_logging_out_one_recruiter_does_not_revoke_another_recruiters_token(self, client, logout_fixtures):
        login_a = _login(client, logout_fixtures["recruiter_a"])
        login_b = _login(client, logout_fixtures["recruiter_b"])

        _logout(client, login_a["access_token"])

        # Recruiter A's own refresh token is now dead...
        assert _refresh(client, login_a["refresh_token"]).status_code == 401
        # ...but Recruiter B, a completely different account, is unaffected.
        still_works = _refresh(client, login_b["refresh_token"])
        assert still_works.status_code == 200
        assert still_works.json()["data"]["role"] == "recruiter"

    def test_a_still_logged_in_account_can_still_refresh(self, client, logout_fixtures):
        """G-01's flow must still work end to end for anyone who has NOT
        logged out -- this change must not break refresh in general."""
        login_data = _login(client, logout_fixtures["candidate"])

        resp = _refresh(client, login_data["refresh_token"])

        assert resp.status_code == 200
        assert resp.json()["data"]["role"] == "candidate"


class TestLogoutRequiresAuthentication:
    def test_logout_without_a_token_is_rejected(self, client):
        resp = client.post("/api/auth/logout")

        assert resp.status_code in (401, 403)

    def test_logout_with_a_raw_refresh_token_is_rejected(self, client, logout_fixtures):
        """A refresh token is not a JWT and must never be accepted by any
        endpoint that authenticates via decode_jwt(), including logout."""
        login_data = _login(client, logout_fixtures["recruiter_a"])

        resp = _logout(client, login_data["refresh_token"])

        assert resp.status_code == 401
