import pytest
from fastapi.testclient import TestClient
from pymongo import MongoClient
from app.config.settings import settings
from app.main import app
from app.auth.jwt_handler import hash_password

@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c

@pytest.fixture(scope="module")
def seed_user():
    sync_client = MongoClient(settings.MONGO_URI)
    db = sync_client[settings.DATABASE_NAME]
    users = db.get_collection("users")
    
    test_email = "candidate_smoke@intellihire.dev"
    test_password = "TestCandidate123!"
    
    # Clean up before
    users.delete_one({"email": test_email})
    
    # Create user
    user_doc = {
        "email": test_email,
        "password_hash": hash_password(test_password),
        "role": "candidate",
        "is_active": True
    }
    users.insert_one(user_doc)
    
    yield {"email": test_email, "password": test_password}
    
    # Clean up after
    users.delete_one({"email": test_email})
    sync_client.close()

@pytest.mark.integration
def test_smoke_candidate_login(client, seed_user):
    """
    Integration test for candidate authentication.
    It creates a temporary seeded user, hits the real auth endpoint, and verifies token reception.
    """
    
    # Test valid login
    resp = client.post("/api/auth/login", json={
        "email": seed_user["email"],
        "password": seed_user["password"]
    })
    
    assert resp.status_code == 200, f"Login failed: {resp.text}"
    data = resp.json().get("data", {})
    assert "access_token" in data
    assert data["role"] == "candidate"

@pytest.mark.integration
def test_smoke_invalid_user_login(client):
    """
    Test that an invalid user returns a 404 (Contract as defined by AuthService).
    """
    resp = client.post("/api/auth/login", json={
        "email": "does_not_exist@intellihire.dev",
        "password": "WrongPassword!"
    })
    
    # Per AuthService contract, if user doesn't exist and company doesn't exist, it returns 404.
    assert resp.status_code == 404
    assert resp.json()["message"] == "Company account not found."
