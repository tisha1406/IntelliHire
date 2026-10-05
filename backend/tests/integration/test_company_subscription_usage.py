"""
Regression: calculate_company_usage() (backend/app/api/company/company_subscription.py)
queried the misspelled collection `interviewcampaigns` instead of the
canonical `interview_campaigns`, so a company's reported campaign usage was
always 0 regardless of how many real campaigns it had.

Fix: `db.interviewcampaigns` -> `db.interview_campaigns`.

This test drives the real GET /company/subscription endpoint (which calls
calculate_company_usage() internally) against the real test database
(tests/conftest.py forces DATABASE_NAME=intellihire_test), with real
documents in `interview_campaigns`, not mocks.

Task 13 regression: GET /company/subscription/options (same file,
get_subscription_options()) returned hardcoded, wrong language/voice lists
("Spanish"/"French"/"German", missing "Gujarati"; "Aditi"/"Raveena"/etc.,
none of which are real IntelliHire voices). Fixed to read the real
`languages`/`voices` master-data collections (populated by Task 12) and
extract only their `name` field. The tests below drive the same real
endpoint against the same real test database.
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
def company_with_campaigns(client):
    sync_client = MongoClient(settings.MONGO_URI)
    db = sync_client[settings.DATABASE_NAME]

    email = "usage-regression-co@example.com"
    db.companies.delete_many({"general.contact_email": email})
    db.interview_campaigns.delete_many({"company_id": "usage-regression-co-id"})

    company_id = db.companies.insert_one({
        "general": {"name": "Usage Regression Co", "contact_email": email},
        "subscription": {"plan": "Enterprise", "status": "active", "billing_cycle": "annual",
                         "expiry_date": None, "seat_count": 5},
        "limits": {"max_recruiters": 5, "max_candidates": 500, "max_campaigns": 10},
        "features": {}, "status": "active", "deleted_at": None,
    }).inserted_id

    # interview_campaigns stores company_id as an ObjectId (confirmed:
    # app/api/company/campaigns.py's create handler does
    # campaign["company_id"] = ObjectId(current_user.sub)), matching what
    # calculate_company_usage() queries for (comp_oid = ObjectId(company_id)).
    campaign_ids = db.interview_campaigns.insert_many([
        {"company_id": company_id, "name": "Campaign A", "status": "active"},
        {"company_id": company_id, "name": "Campaign B", "status": "active"},
        {"company_id": company_id, "name": "Campaign C", "status": "active"},
    ]).inserted_ids

    yield {"company_id": str(company_id)}

    db.companies.delete_many({"_id": company_id})
    db.interview_campaigns.delete_many({"_id": {"$in": campaign_ids}})
    sync_client.close()


def _company_headers(company_id):
    token = create_access_token(user_id=company_id, role="company", company_id=company_id)
    return {"Authorization": f"Bearer {token}"}


def test_campaign_usage_counts_real_interview_campaigns_documents(client, company_with_campaigns):
    company_id = company_with_campaigns["company_id"]

    resp = client.get("/company/subscription", headers=_company_headers(company_id))

    assert resp.status_code == 200, resp.text
    usage = resp.json()["data"]["usage"]
    assert usage["campaigns"] == 3


def test_the_misspelled_collection_would_have_reported_zero(company_with_campaigns):
    """Directly proves the old bug: the real 3 campaigns exist in
    `interview_campaigns`, but querying the misspelled `interviewcampaigns`
    (no underscore) collection -- what the code used before this fix --
    finds nothing, because nothing has ever written to that collection."""
    sync_client = MongoClient(settings.MONGO_URI)
    db = sync_client[settings.DATABASE_NAME]
    company_oid = ObjectId(company_with_campaigns["company_id"])

    real_count = db.interview_campaigns.count_documents({"company_id": company_oid})
    misspelled_count = db.interviewcampaigns.count_documents({"company_id": company_oid})

    assert real_count == 3
    assert misspelled_count == 0
    sync_client.close()


class TestSubscriptionOptionsLanguagesAndVoices:
    """Task 13: GET /company/subscription/options must return the real
    master-data languages/voices (populated by Task 12's bootstrap -- see
    app/db/bootstrap.py -- which runs automatically whenever the app starts,
    including under this module's `client` fixture), not the old hardcoded
    ["English","Hindi","Spanish","French","German"] /
    ["Aditi","Raveena","Joanna","Matthew","Brian"] lists. No fixture seeding
    is needed here: the collections are guaranteed populated by the app's
    own startup bootstrap, exactly as they are in the real dev database.
    """

    def test_languages_are_the_three_finalized_names_only(self, client):
        resp = client.get(
            "/company/subscription/options",
            headers=_company_headers("000000000000000000000000"),
        )

        assert resp.status_code == 200, resp.text
        languages = resp.json()["data"]["config_options"]["languages"]
        assert sorted(languages) == sorted(["English", "Hindi", "Gujarati"])

    def test_voices_are_the_five_finalized_names_only(self, client):
        resp = client.get(
            "/company/subscription/options",
            headers=_company_headers("000000000000000000000000"),
        )

        voices = resp.json()["data"]["config_options"]["voices"]
        assert sorted(voices) == sorted(["shubh", "simran", "rohan", "ishita", "sunny"])

    def test_response_shape_and_untouched_fields_are_preserved(self, client):
        resp = client.get(
            "/company/subscription/options",
            headers=_company_headers("000000000000000000000000"),
        )

        data = resp.json()["data"]
        assert set(data.keys()) == {"features", "limits", "billing_cycles", "config_options"}
        config_options = data["config_options"]
        assert set(config_options.keys()) == {"languages", "voices", "llm_tiers", "interview_modes"}
        # llm_tiers / interview_modes are explicitly out of Task 13's scope -- unchanged.
        assert config_options["llm_tiers"] == ["Groq", "OpenAI", "Anthropic", "Gemini"]
        assert config_options["interview_modes"] == ["Balanced", "Structured", "Technical", "Behavioral", "Stress"]

    def test_only_the_name_field_is_returned_no_codes_or_providers(self, client):
        resp = client.get(
            "/company/subscription/options",
            headers=_company_headers("000000000000000000000000"),
        )

        config_options = resp.json()["data"]["config_options"]
        assert all(isinstance(v, str) for v in config_options["languages"])
        assert all(isinstance(v, str) for v in config_options["voices"])
        # None of the real documents' other fields ("code", "provider", "_id") leak through.
        assert "en" not in config_options["languages"] and "gu" not in config_options["languages"]
        assert "Sarvam AI" not in config_options["voices"]

    def test_the_endpoint_does_not_mutate_the_database(self, client):
        sync_client = MongoClient(settings.MONGO_URI)
        db = sync_client[settings.DATABASE_NAME]
        before_languages = list(db.languages.find({}))
        before_voices = list(db.voices.find({}))

        client.get("/company/subscription/options", headers=_company_headers("000000000000000000000000"))

        assert list(db.languages.find({})) == before_languages
        assert list(db.voices.find({})) == before_voices
        sync_client.close()
