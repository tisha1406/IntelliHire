"""
G-01 regression: real end-to-end refresh-token flow against the real FastAPI
app and the isolated test MongoDB (tests/conftest.py forces
DATABASE_NAME=intellihire_test).

specs.md Section 20 confirmed the prior state: "POST /api/auth/refresh
ignores all input and always returns the literal string 'new_token_here'" --
the server-stored hashed refresh token was never actually validated or used.

These tests drive the real /api/auth/login and /api/auth/refresh endpoints
(not mocks) and prove:
  * a valid refresh token issues a working new access token and rotates the
    refresh token,
  * an expired refresh token is rejected,
  * a refresh token, once used, cannot be reused (rotation),
  * role/identity claims survive a refresh unchanged,
  * a raw refresh token is never accepted in place of an access token.

Fixture setup uses a plain synchronous pymongo.MongoClient (same pattern as
tests/integration/test_auth_smoke.py), not the async repositories: the
TestClient's app lifespan opens its own motor client bound to its own event
loop, and an async fixture on pytest-asyncio's separate loop cannot share it
(cross-loop motor calls raise RuntimeError). Going straight through pymongo
sidesteps that entirely and keeps this a real, non-mocked integration test.
"""
from datetime import UTC, datetime, timedelta

from bson import ObjectId
from fastapi.testclient import TestClient
from jose import jwt
from pymongo import MongoClient
import pytest

from app.auth.jwt_handler import hash_password
from app.config.settings import settings
from app.main import app


def _decode(token: str) -> dict:
    return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def refresh_fixtures(client):
    sync_client = MongoClient(settings.MONGO_URI)
    db = sync_client[settings.DATABASE_NAME]

    for coll, query in (
        ("companies", {"general.contact_email": "g01-company@example.com"}),
        ("users", {"email": {"$in": ["g01-recruiter@example.com", "g01-candidate@example.com"]}}),
        ("candidates", {"email": "g01-candidate@example.com"}),
        ("campaigns", {"name": "G01 Role"}),
    ):
        db[coll].delete_many(query)

    company_id = db.companies.insert_one({
        "general": {"name": "G01 Verify Co", "contact_email": "g01-company@example.com"},
        "credentials": {"password_hash": hash_password("CompanyPass123!")},
        "status": "active",
    }).inserted_id

    campaign_id = db.campaigns.insert_one({
        "company_id": company_id, "name": "G01 Role", "job_position": "Engineer", "status": "active",
    }).inserted_id

    recruiter_id = db.users.insert_one({
        "name": "G01 Recruiter", "email": "g01-recruiter@example.com",
        "password_hash": hash_password("RecruiterPass123!"),
        "role": "recruiter", "company_id": company_id,
        "is_active": True, "must_change_password": False, "recruiter_id": str(ObjectId()),
    }).inserted_id

    candidate_user_id = db.users.insert_one({
        "email": "g01-candidate@example.com",
        "password_hash": hash_password("CandidatePass123!"),
        "role": "candidate", "company_id": company_id,
        "is_active": True, "must_change_password": False,
    }).inserted_id

    candidate_id = db.candidates.insert_one({
        "user_id": candidate_user_id, "company_id": company_id, "campaign_id": campaign_id,
        "name": "G01 Candidate", "email": "g01-candidate@example.com",
        "target_role": "Engineer", "status": "active",
    }).inserted_id

    db.users.update_one({"_id": candidate_user_id}, {"$set": {"candidate_id": candidate_id}})

    yield {
        "db": db,
        "company": {"email": "g01-company@example.com", "password": "CompanyPass123!"},
        "recruiter": {"email": "g01-recruiter@example.com", "password": "RecruiterPass123!"},
        "candidate": {"email": "g01-candidate@example.com", "password": "CandidatePass123!"},
    }

    db.candidates.delete_many({"_id": candidate_id})
    db.users.delete_many({"_id": {"$in": [recruiter_id, candidate_user_id]}})
    db.campaigns.delete_many({"_id": campaign_id})
    db.companies.delete_many({"_id": company_id})
    sync_client.close()


def _login(client, creds):
    resp = client.post("/api/auth/login", json=creds)
    assert resp.status_code == 200, resp.text
    return resp.json()["data"]


class TestValidRefresh:
    def test_valid_refresh_issues_a_working_access_token_for_the_same_identity(self, client, refresh_fixtures):
        login_data = _login(client, refresh_fixtures["recruiter"])

        resp = client.post("/api/auth/refresh", json={"refresh_token": login_data["refresh_token"]})

        assert resp.status_code == 200, resp.text
        data = resp.json()["data"]
        assert data["token_type"] == "bearer"
        assert data["role"] == "recruiter"
        new_claims = _decode(data["access_token"])
        assert new_claims["sub"] == _decode(login_data["access_token"])["sub"]

        # the new access token actually authenticates a real protected endpoint
        me = client.get("/admin/profile", headers={"Authorization": f"Bearer {data['access_token']}"})
        assert me.status_code == 403  # recruiter is not admin -- proves the token is valid and its role is enforced

    def test_valid_refresh_rotates_the_refresh_token(self, client, refresh_fixtures):
        login_data = _login(client, refresh_fixtures["recruiter"])

        resp = client.post("/api/auth/refresh", json={"refresh_token": login_data["refresh_token"]})

        assert resp.json()["data"]["refresh_token"] != login_data["refresh_token"]

    def test_role_and_identity_claims_survive_a_refresh(self, client, refresh_fixtures):
        login_data = _login(client, refresh_fixtures["candidate"])
        original_claims = _decode(login_data["access_token"])

        resp = client.post("/api/auth/refresh", json={"refresh_token": login_data["refresh_token"]})

        new_claims = _decode(resp.json()["data"]["access_token"])
        assert new_claims["sub"] == original_claims["sub"]
        assert new_claims["role"] == original_claims["role"] == "candidate"
        assert new_claims["candidate_id"] == original_claims["candidate_id"]
        assert new_claims["company_id"] == original_claims["company_id"]
        assert new_claims["campaign_id"] == original_claims["campaign_id"]
        assert new_claims["name"] == original_claims["name"] == "G01 Candidate"
        assert new_claims["email"] == original_claims["email"]

    def test_company_login_can_also_refresh(self, client, refresh_fixtures):
        login_data = _login(client, refresh_fixtures["company"])

        resp = client.post("/api/auth/refresh", json={"refresh_token": login_data["refresh_token"]})

        assert resp.status_code == 200, resp.text
        assert resp.json()["data"]["role"] == "company"


class TestInvalidAndExpiredRefresh:
    def test_garbage_refresh_token_is_rejected(self, client):
        resp = client.post("/api/auth/refresh", json={"refresh_token": "this-was-never-issued"})

        assert resp.status_code == 401

    def test_empty_refresh_token_is_rejected(self, client):
        resp = client.post("/api/auth/refresh", json={"refresh_token": ""})

        assert resp.status_code == 401

    def test_expired_refresh_token_is_rejected(self, client, refresh_fixtures):
        login_data = _login(client, refresh_fixtures["recruiter"])

        # Backdate the stored expiry directly in the DB -- simulates time
        # having passed past REFRESH_TOKEN_EXPIRE_DAYS without waiting days.
        refresh_fixtures["db"].users.update_many(
            {"email": refresh_fixtures["recruiter"]["email"]},
            {"$set": {"refresh_token_expires_at": datetime.now(UTC) - timedelta(days=1)}},
        )

        resp = client.post("/api/auth/refresh", json={"refresh_token": login_data["refresh_token"]})

        assert resp.status_code == 401


class TestRefreshTokenCannotBeReusedOrMisusedAsAccessToken:
    def test_a_used_refresh_token_cannot_be_reused(self, client, refresh_fixtures):
        login_data = _login(client, refresh_fixtures["recruiter"])

        first = client.post("/api/auth/refresh", json={"refresh_token": login_data["refresh_token"]})
        assert first.status_code == 200

        second = client.post("/api/auth/refresh", json={"refresh_token": login_data["refresh_token"]})

        assert second.status_code == 401

    def test_raw_refresh_token_is_never_accepted_as_an_access_token(self, client, refresh_fixtures):
        login_data = _login(client, refresh_fixtures["recruiter"])

        resp = client.get("/admin/profile", headers={"Authorization": f"Bearer {login_data['refresh_token']}"})

        # The refresh token is an opaque random string, not a JWT: decode_jwt
        # must reject it outright (401), never 403 (which would imply it was
        # successfully decoded and merely lacked the admin role).
        assert resp.status_code == 401
