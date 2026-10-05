"""
Regression for the Task 11 audit's confirmed finding: Admin Activate
(POST /admin/companies/{id}/activate -> CompanyService.activate_company())
used to perform an unconditional {"subscription.status": "active"} write,
letting an admin activate a company that had never paid -- no Payment, no
SubscriptionHistory, no expiry date -- from ANY status, including
pending_verification/pending_payment (the states the real payment
verification flow owns).

Fix: activate_company() now only allows the transition
suspended -> active; every other current status is rejected with 400
before any write happens. The real payment flow
(app/api/company/company_subscription.py) is completely untouched.

These tests drive the real FastAPI app and real endpoints
(POST /admin/companies/{id}/activate, POST /admin/companies/{id}/suspend)
against the real test database (tests/conftest.py forces
DATABASE_NAME=intellihire_test) -- not mocks.
"""
from bson import ObjectId
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


@pytest.fixture
def db():
    sync_client = MongoClient(settings.MONGO_URI)
    database = sync_client[settings.DATABASE_NAME]
    yield database
    sync_client.close()


def _make_company(db, status, email):
    db.companies.delete_many({"general.contact_email": email})
    company_id = db.companies.insert_one({
        "general": {"name": "Activate Guard Regression Co", "contact_email": email},
        "subscription": {"plan": "Enterprise", "status": status, "billing_cycle": "annual",
                         "start_date": None, "expiry_date": "", "seat_count": 5},
        "limits": {"max_recruiters": 5, "max_candidates": 500, "max_campaigns": 10},
        "features": {}, "status": status, "deleted_at": None,
    }).inserted_id
    return company_id


def _admin_headers():
    token = create_access_token(user_id="000000000000000000000000", role="admin")
    return {"Authorization": f"Bearer {token}"}


def _status_of(db, company_id):
    return db.companies.find_one({"_id": company_id})["subscription"]["status"]


def _cleanup(db, company_id):
    db.companies.delete_many({"_id": company_id})


class TestSuspendedCanBeReactivated:
    def test_suspended_to_active_succeeds(self, client, db):
        company_id = _make_company(db, "suspended", "activate-guard-suspended@example.com")
        try:
            resp = client.post(f"/admin/companies/{company_id}/activate", headers=_admin_headers())

            assert resp.status_code == 200, resp.text
            assert _status_of(db, company_id) == "active"
        finally:
            _cleanup(db, company_id)

    def test_the_existing_suspend_then_activate_workflow_still_works(self, client, db):
        company_id = _make_company(db, "active", "activate-guard-roundtrip@example.com")
        try:
            suspend_resp = client.post(f"/admin/companies/{company_id}/suspend", headers=_admin_headers())
            assert suspend_resp.status_code == 200, suspend_resp.text
            assert _status_of(db, company_id) == "suspended"

            activate_resp = client.post(f"/admin/companies/{company_id}/activate", headers=_admin_headers())
            assert activate_resp.status_code == 200, activate_resp.text
            assert _status_of(db, company_id) == "active"
        finally:
            _cleanup(db, company_id)


class TestNonSuspendedStatusesAreRejected:
    @pytest.mark.parametrize("blocked_status", [
        "pending_verification", "pending_payment", "expired", "cancelled", "trial", "active",
    ])
    def test_activate_is_rejected_and_status_is_unchanged(self, client, db, blocked_status):
        email = f"activate-guard-{blocked_status}@example.com"
        company_id = _make_company(db, blocked_status, email)
        try:
            resp = client.post(f"/admin/companies/{company_id}/activate", headers=_admin_headers())

            assert resp.status_code == 400, resp.text
            assert _status_of(db, company_id) == blocked_status  # unchanged -- no write happened
        finally:
            _cleanup(db, company_id)
