"""
Regression for the confirmed Admin Company Provisioning blocker.

Root cause: GET /admin/settings/master built each interview mode's display
name from `m.get("display_name")`, but interview_mode_definitions documents
only ever have a `name` field (confirmed against the real
scripts/seed_dev_data.py::seed_interview_modes() shape and the real dev
database). This made every interview_modes[i].name null in the API response.
CompanyWizard (frontend/src/components/admin/CompanyWizard/index.jsx) then
auto-populates allowed_interview_modes: config.interview_modes.map(m => m.name)
on every new provisioning session -- [null, null, null, null] -- which fails
the frontend's `z.array(z.string())` schema with zero visible UI error
(the Interview Modes tab has no error indicator), silently blocking
handleSubmit(onSubmit) before POST /admin/companies is ever called.

Fix: read `m.get("name")` instead. This file proves the real endpoint and
the real provisioning POST both work end to end against the real test
database (tests/conftest.py forces DATABASE_NAME=intellihire_test), not
mocks.

Fixture setup uses a plain synchronous pymongo.MongoClient (same pattern as
tests/integration/test_auth_refresh_flow.py / test_auth_logout_revocation.py):
the TestClient's app lifespan opens its own motor client bound to its own
event loop, and an async fixture on pytest-asyncio's separate loop cannot
share it.
"""
from fastapi.testclient import TestClient
from pymongo import MongoClient
import pytest

from app.auth.jwt_handler import create_access_token
from app.config.settings import settings
from app.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def real_interview_modes(client):
    """Seeds the exact real shape (an interview_mode_definitions document
    with a `name` field, no `display_name`) -- the same shape
    scripts/seed_dev_data.py and the real dev database use -- then cleans
    up afterward."""
    sync_client = MongoClient(settings.MONGO_URI)
    db = sync_client[settings.DATABASE_NAME]

    specs = [
        {"mode_id": "regr_balanced", "name": "Regression Balanced", "description": "Standard balanced interview approach."},
        {"mode_id": "regr_structured", "name": "Regression Structured", "description": "Strict structured interview."},
    ]
    db.interview_mode_definitions.delete_many({"mode_id": {"$in": [s["mode_id"] for s in specs]}})

    docs = [{
        **s, "version": 1, "status": "published",
        "settings": {"allowed_question_types": ["initial"]},
        "created_by": "test", "published_at": None,
    } for s in specs]
    result = db.interview_mode_definitions.insert_many(docs)

    yield {s["mode_id"]: s["name"] for s in specs}

    db.interview_mode_definitions.delete_many({"_id": {"$in": result.inserted_ids}})
    sync_client.close()


def _admin_headers():
    token = create_access_token(user_id="000000000000000000000000", role="admin")
    return {"Authorization": f"Bearer {token}"}


class TestMasterSettingsInterviewModeNames:
    def test_interview_mode_names_are_not_null(self, client, real_interview_modes):
        resp = client.get("/admin/settings/master", headers=_admin_headers())

        assert resp.status_code == 200, resp.text
        modes = resp.json()["data"]["interview_modes"]
        assert len(modes) >= len(real_interview_modes)
        assert all(m["name"] is not None for m in modes)

    def test_interview_mode_names_match_real_documents(self, client, real_interview_modes):
        resp = client.get("/admin/settings/master", headers=_admin_headers())

        names = {m["name"] for m in resp.json()["data"]["interview_modes"]}
        for expected_name in real_interview_modes.values():
            assert expected_name in names

    def test_other_master_settings_fields_are_unchanged(self, client, real_interview_modes):
        resp = client.get("/admin/settings/master", headers=_admin_headers())

        data = resp.json()["data"]
        assert set(data.keys()) == {
            "ai_models", "features", "security_policies", "languages", "voices", "strategies", "interview_modes",
        }
        assert isinstance(data["ai_models"], list) and len(data["ai_models"]) > 0
        assert isinstance(data["features"], list) and len(data["features"]) > 0
        assert isinstance(data["strategies"], list)
        # The interview_modes entries still carry every field they carried before the fix,
        # only `name` changed from always-null to the real value.
        for m in data["interview_modes"]:
            assert set(m.keys()) == {
                "id", "name", "description", "duration", "difficulty", "question_strategy", "enabled", "is_default",
            }

    def test_company_wizard_can_build_a_valid_allowed_interview_modes_array(self, client, real_interview_modes):
        """Proxy for the frontend's `config.interview_modes.map(m => m.name)` /
        `z.array(z.string())` check: every resulting name must be a non-null
        string, which is exactly what z.array(z.string()) requires."""
        resp = client.get("/admin/settings/master", headers=_admin_headers())

        allowed_interview_modes = [m["name"] for m in resp.json()["data"]["interview_modes"]]
        assert all(isinstance(name, str) for name in allowed_interview_modes)


class TestProvisioningReachableWithRealWizardData:
    def test_post_admin_companies_succeeds_with_a_schema_valid_wizard_payload(self, client, real_interview_modes):
        """End-to-end: build the exact payload CompanyWizard would now send
        (allowed_interview_modes populated from the real, non-null names)
        and confirm POST /admin/companies is actually reached and succeeds --
        this is the request that was previously never sent at all."""
        sync_client = MongoClient(settings.MONGO_URI)
        db = sync_client[settings.DATABASE_NAME]
        email = "wizard-regression-co@example.com"
        db.companies.delete_many({"general.contact_email": email})

        payload = {
            "general": {"name": "Wizard Regression Co", "contact_email": email},
            "subscription": {"plan": "Enterprise", "status": "active", "billing_cycle": "annual", "seat_count": 5},
            "limits": {"max_recruiters": 5, "max_candidates": 500, "max_campaigns": 10, "monthly_interviews": 100,
                       "concurrent_interviews": 5, "storage_limit_gb": 10.0, "api_requests_per_month": 10000,
                       "ai_credits": 1000, "resume_uploads": 5000},
            "security": {"login_enabled": True, "mfa_required": False, "password_policy": "standard",
                         "session_timeout_minutes": 60, "jwt_lifetime_hours": 24, "refresh_token_lifetime_days": 7,
                         "sso_enabled": False, "allowed_domains": [], "ip_whitelist": [],
                         "concurrent_sessions_allowed": 3, "remember_me_allowed": True,
                         "login_attempts_before_lockout": 5},
            "features": {},
            "allowed_languages": [], "allowed_voices": [], "allowed_strategies": [],
            "allowed_interview_modes": list(real_interview_modes.values()),  # the previously-impossible non-null array
            "allowed_llm_tiers": [],
        }

        try:
            resp = client.post("/admin/companies", json=payload, headers=_admin_headers())
            assert resp.status_code == 201, resp.text
            body = resp.json()
            assert body["success"] is True
            assert body["data"]["company_id"]
        finally:
            db.companies.delete_many({"general.contact_email": email})
            sync_client.close()
