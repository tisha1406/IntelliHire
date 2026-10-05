"""
Regression for the confirmed payment-verification bug (Task 9 audit):

POST /company/subscription/payment/verify never checked a Payment's own
`amount` against anything authoritative. Real database evidence found two
`payment_type: "initial"` Payment documents for the same company -- one for
the real price (INR 128620, left stuck at status "pending"), and a second
for INR 0 that was verified and successfully activated the subscription.

Fix: before calling PaymentService.verify_payment() (which is what marks a
Payment "success" and is shared with the untouched renewal/upgrade verify
endpoints -- not modified here), the route now looks up the Payment by
`order_id` and requires its stored `amount` to equal the company's own
`subscription.pricing.total` (the same authoritative figure
create_payment_order() is always supposed to be called with). A mismatch
raises 400 before the provider is ever invoked, so the Payment is never
marked successful and the subscription is never activated.

These tests drive the real FastAPI app and real endpoints
(POST /company/subscription/payment/order, POST .../payment/verify) against
the real test database (tests/conftest.py forces
DATABASE_NAME=intellihire_test) -- not mocks.
"""
from fastapi.testclient import TestClient
from pymongo import MongoClient
import pytest

from app.auth.jwt_handler import create_access_token
from app.config.settings import settings
from app.main import app

AUTHORITATIVE_TOTAL = 128620.0


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture
def pending_payment_company(client):
    sync_client = MongoClient(settings.MONGO_URI)
    db = sync_client[settings.DATABASE_NAME]

    email = "payment-verify-regression-co@example.com"
    db.companies.delete_many({"general.contact_email": email})

    company_id = db.companies.insert_one({
        "general": {"name": "Payment Verify Regression Co", "contact_email": email},
        "subscription": {
            "plan": "Enterprise", "status": "pending_payment", "billing_cycle": "annual",
            "start_date": None, "expiry_date": "", "seat_count": 5,
            "pricing": {"base_price": 50000.0, "feature_cost": 55000.0, "limit_cost": 4000.0,
                       "discount": 0.0, "tax": 19620.0, "total": AUTHORITATIVE_TOTAL, "currency": "INR"},
        },
        "limits": {"max_recruiters": 5, "max_candidates": 500, "max_campaigns": 10},
        "features": {}, "status": "pending_payment", "deleted_at": None,
    }).inserted_id

    yield {"company_id": str(company_id), "db": db}

    db.payments.delete_many({"company_id": str(company_id)})
    db.subscription_history.delete_many({"company_id": str(company_id)})
    db.companies.delete_many({"_id": company_id})
    sync_client.close()


def _company_headers(company_id):
    token = create_access_token(user_id=company_id, role="company", company_id=company_id)
    return {"Authorization": f"Bearer {token}"}


def _create_order(client, company_id, amount):
    resp = client.post(
        "/company/subscription/payment/order",
        json={"amount": amount, "currency": "INR"},
        headers=_company_headers(company_id),
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["data"]["id"]


def _verify(client, company_id, order_id):
    return client.post(
        "/company/subscription/payment/verify",
        json={"order_id": order_id},
        headers=_company_headers(company_id),
    )


def _get_payment(db, order_id):
    return db.payments.find_one({"order_id": order_id})


def _get_subscription_status(db, company_id):
    from bson import ObjectId
    company = db.companies.find_one({"_id": ObjectId(company_id)})
    return company["subscription"]["status"]


class TestCorrectlyPricedPaymentStillActivates:
    def test_a_correctly_priced_payment_activates_the_subscription(self, client, pending_payment_company):
        company_id = pending_payment_company["company_id"]
        db = pending_payment_company["db"]
        order_id = _create_order(client, company_id, AUTHORITATIVE_TOTAL)

        resp = _verify(client, company_id, order_id)

        assert resp.status_code == 200, resp.text
        assert _get_subscription_status(db, company_id) == "active"
        payment = _get_payment(db, order_id)
        assert payment["status"] == "success"
        assert payment["verified_at"] is not None


class TestZeroAndMismatchedAmountsAreRejected:
    def test_a_zero_amount_payment_cannot_activate_a_non_zero_subscription(self, client, pending_payment_company):
        company_id = pending_payment_company["company_id"]
        db = pending_payment_company["db"]
        order_id = _create_order(client, company_id, 0.0)  # exactly the reported real-world bug

        resp = _verify(client, company_id, order_id)

        assert resp.status_code == 400
        assert _get_subscription_status(db, company_id) == "pending_payment"  # unchanged, not "active"
        payment = _get_payment(db, order_id)
        assert payment["status"] == "pending"  # never marked successful
        assert payment.get("verified_at") is None

    def test_a_mismatched_amount_cannot_activate_the_subscription(self, client, pending_payment_company):
        company_id = pending_payment_company["company_id"]
        db = pending_payment_company["db"]
        order_id = _create_order(client, company_id, AUTHORITATIVE_TOTAL / 2)  # underpaid, not zero

        resp = _verify(client, company_id, order_id)

        assert resp.status_code == 400
        assert _get_subscription_status(db, company_id) == "pending_payment"
        payment = _get_payment(db, order_id)
        assert payment["status"] == "pending"
        assert payment.get("verified_at") is None

    def test_failed_amount_validation_never_sets_expiry_or_start_dates(self, client, pending_payment_company):
        company_id = pending_payment_company["company_id"]
        db = pending_payment_company["db"]
        order_id = _create_order(client, company_id, 0.0)

        _verify(client, company_id, order_id)

        from bson import ObjectId
        company = db.companies.find_one({"_id": ObjectId(company_id)})
        assert company["subscription"]["start_date"] is None
        assert company["subscription"]["expiry_date"] == ""
