import pytest
from fastapi.testclient import TestClient
from typing import Dict, Any

from app.auth.jwt_handler import create_access_token
from app.rbac.models import UserRole
from app.main import app

@pytest.fixture
def client():
    with TestClient(app) as client:
        yield client

@pytest.fixture
def admin_token() -> str:
    return create_access_token(user_id="admin_user", role=UserRole.ADMIN.value)

@pytest.fixture
def company_token() -> str:
    return create_access_token(user_id="company_user", role=UserRole.COMPANY.value)

def get_base_strategy_payload() -> Dict[str, Any]:
    return {
        "strategy_id": "test_strat_1",
        "name": "Test Strategy",
        "description": "A test strategy definition",
        "applicable_interview_types": ["technical"],
        "min_questions": 3,
        "target_questions": 5,
        "max_questions": 7,
        "max_questions_per_topic": 3,
        "max_followups_per_topic": 2,
        "strong_threshold": 0.8,
        "acceptable_threshold": 0.6,
        "weak_threshold": 0.4,
        "topic_selection_policy": {"policy_type": "priority_score"},
        "difficulty_policy": {
            "adapts": True,
            "scope": "per_topic",
            "reset_on_switch": True,
            "step_size": 1,
            "band_constrainable": True
        },
        "followup_policy": {
            "allowed_categories": ["followup_depth", "followup_clarification"],
            "max_per_topic": 2
        },
        "gap_policy": {
            "enabled": True,
            "max_share_of_budget": 0.4
        },
        "completion_policy": {
            "allow_early_exit": True,
            "require_all_critical_covered": True
        },
        "company_override_bounds": {
            "target_questions_min_delta": 0,
            "target_questions_max_delta": 0,
            "allowed_difficulty_bands": []
        }
    }

import uuid

def test_admin_create_strategy(client: TestClient, admin_token: str):
    headers = {"Authorization": f"Bearer {admin_token}"}
    payload = get_base_strategy_payload()
    uid = str(uuid.uuid4())
    payload["strategy_id"] = uid
    
    response = client.post("/admin/strategies/", json=payload, headers=headers)
    assert response.status_code == 201
    
    data = response.json()
    assert data["data"]["strategy_id"] == uid
    assert data["data"]["version"] == 1
    assert data["data"]["is_active"] is True

def test_company_cannot_create_strategy(client: TestClient, company_token: str):
    headers = {"Authorization": f"Bearer {company_token}"}
    payload = get_base_strategy_payload()
    response = client.post("/admin/strategies/", json=payload, headers=headers)
    assert response.status_code == 403

def test_cannot_create_duplicate_strategy(client: TestClient, admin_token: str):
    headers = {"Authorization": f"Bearer {admin_token}"}
    payload = get_base_strategy_payload()
    uid = str(uuid.uuid4())
    payload["strategy_id"] = uid
    
    res1 = client.post("/admin/strategies/", json=payload, headers=headers)
    assert res1.status_code == 201
    
    res2 = client.post("/admin/strategies/", json=payload, headers=headers)
    assert res2.status_code == 409

def test_create_new_version(client: TestClient, admin_token: str):
    headers = {"Authorization": f"Bearer {admin_token}"}
    payload = get_base_strategy_payload()
    uid = str(uuid.uuid4())
    payload["strategy_id"] = uid
    
    res1 = client.post("/admin/strategies/", json=payload, headers=headers)
    assert res1.status_code == 201
    
    # Create version 2
    payload["name"] = "Test Strategy V2"
    payload["target_questions"] = 6
    res2 = client.post(f"/admin/strategies/{uid}/versions", json=payload, headers=headers)
    assert res2.status_code == 201
    
    data = res2.json()
    assert data["data"]["version"] == 2
    assert data["data"]["target_questions"] == 6

def test_list_strategies_latest_only(client: TestClient, admin_token: str):
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Create two versions of strat3
    payload = get_base_strategy_payload()
    uid3 = str(uuid.uuid4())
    payload["strategy_id"] = uid3
    
    client.post("/admin/strategies/", json=payload, headers=headers)
    client.post(f"/admin/strategies/{uid3}/versions", json=payload, headers=headers)
    
    # Create strat4
    payload4 = get_base_strategy_payload()
    uid4 = str(uuid.uuid4())
    payload4["strategy_id"] = uid4
    client.post("/admin/strategies/", json=payload4, headers=headers)
    
    response = client.get("/admin/strategies/", headers=headers)
    assert response.status_code == 200
    
    data = response.json()["data"]
    # We should only get the latest version for each strat
    ids = [d["strategy_id"] for d in data]
    assert uid3 in ids
    
    # Check that strat 3 is version 2
    strat3 = next(d for d in data if d["strategy_id"] == uid3)
    assert strat3["version"] == 2

def test_list_strategy_versions(client: TestClient, admin_token: str):
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    uid = str(uuid.uuid4())
    payload = get_base_strategy_payload()
    payload["strategy_id"] = uid
    client.post("/admin/strategies/", json=payload, headers=headers)
    client.post(f"/admin/strategies/{uid}/versions", json=payload, headers=headers)
    
    response = client.get(f"/admin/strategies/{uid}/versions", headers=headers)
    assert response.status_code == 200
    
    data = response.json()["data"]
    assert len(data) == 2
    versions = [d["version"] for d in data]
    assert 1 in versions
    assert 2 in versions

def test_activate_deactivate_version(client: TestClient, admin_token: str):
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    payload = get_base_strategy_payload()
    uid = str(uuid.uuid4())
    payload["strategy_id"] = uid
    client.post("/admin/strategies/", json=payload, headers=headers)
    
    # Deactivate version 1
    patch_payload = {"is_active": False}
    patch_res = client.patch(
        f"/admin/strategies/{uid}/versions/1/activate", 
        json=patch_payload, 
        headers=headers
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["data"]["new_version"] == 1
    
    # Verify it is deactivated
    get_res = client.get(f"/admin/strategies/{uid}/versions/1", headers=headers)
    assert get_res.status_code == 200
    assert get_res.json()["data"]["is_active"] is False

def test_schema_validation(client: TestClient, admin_token: str):
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    payload = get_base_strategy_payload()
    payload["strategy_id"] = "test_strat_invalid"
    # min > max
    payload["min_questions"] = 10
    payload["max_questions"] = 5
    
    res = client.post("/admin/strategies/", json=payload, headers=headers)
    assert res.status_code == 422
