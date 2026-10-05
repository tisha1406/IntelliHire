"""
D-03 integration tests for ScenarioRepository.

Follows the same real-MongoDB convention as
tests/integration/test_seed_interview_modes.py (connect_db/close_db against
the configured dev database), scoped strictly to the "situational_scenarios"
collection -- never touches any other collection.
"""
import pytest

from app.db.mongo import connect_db, close_db
from app.repositories.scenario_repository import ScenarioRepository


@pytest.mark.asyncio
async def test_scenario_repository_active_inactive_and_role_matching():
    await connect_db()
    repo = ScenarioRepository()
    try:
        await repo.collection.delete_many({})

        await repo.create({
            "scenario_id": "b_active", "role_or_domain": "backend engineer",
            "topic_name": "Active Backend Scenario", "scenario_context": "ctx",
            "difficulty": "medium", "is_active": True,
        })
        await repo.create({
            "scenario_id": "a_inactive", "role_or_domain": "backend engineer",
            "topic_name": "Inactive Backend Scenario", "scenario_context": "ctx",
            "difficulty": "medium", "is_active": False,
        })
        await repo.create({
            "scenario_id": "z_other_role", "role_or_domain": "product manager",
            "topic_name": "PM Scenario", "scenario_context": "ctx",
            "difficulty": "easy", "is_active": True,
        })

        results = await repo.get_active_for_role("backend engineer")
        ids = [r["scenario_id"] for r in results]

        assert "b_active" in ids
        assert "a_inactive" not in ids  # inactive excluded
        assert "z_other_role" not in ids  # different role excluded
    finally:
        await repo.collection.delete_many({})
        await close_db()


@pytest.mark.asyncio
async def test_scenario_repository_case_insensitive_and_trimmed_matching():
    await connect_db()
    repo = ScenarioRepository()
    try:
        await repo.collection.delete_many({})
        await repo.create({
            "scenario_id": "fe_001", "role_or_domain": "frontend engineer",
            "topic_name": "FE Scenario", "scenario_context": "ctx",
            "difficulty": "medium", "is_active": True,
        })

        results = await repo.get_active_for_role("  Frontend Engineer  ")
        assert [r["scenario_id"] for r in results] == ["fe_001"]
    finally:
        await repo.collection.delete_many({})
        await close_db()


@pytest.mark.asyncio
async def test_scenario_repository_deterministic_sort_order():
    await connect_db()
    repo = ScenarioRepository()
    try:
        await repo.collection.delete_many({})
        # Insert out of scenario_id order to prove sorting, not insertion order.
        for sid in ["z_sc", "a_sc", "m_sc"]:
            await repo.create({
                "scenario_id": sid, "role_or_domain": "data scientist",
                "topic_name": f"Scenario {sid}", "scenario_context": "ctx",
                "difficulty": "medium", "is_active": True,
            })

        results_1 = await repo.get_active_for_role("data scientist")
        results_2 = await repo.get_active_for_role("data scientist")

        ids_1 = [r["scenario_id"] for r in results_1]
        ids_2 = [r["scenario_id"] for r in results_2]

        assert ids_1 == ["a_sc", "m_sc", "z_sc"]
        assert ids_1 == ids_2  # deterministic across repeated calls
    finally:
        await repo.collection.delete_many({})
        await close_db()


@pytest.mark.asyncio
async def test_scenario_repository_falls_back_to_general_when_no_role_match():
    await connect_db()
    repo = ScenarioRepository()
    try:
        await repo.collection.delete_many({})
        await repo.create({
            "scenario_id": "gen_001", "role_or_domain": "general",
            "topic_name": "General Scenario", "scenario_context": "ctx",
            "difficulty": "easy", "is_active": True,
        })

        results = await repo.get_active_for_role("underwater basket weaver")
        assert [r["scenario_id"] for r in results] == ["gen_001"]
    finally:
        await repo.collection.delete_many({})
        await close_db()


@pytest.mark.asyncio
async def test_scenario_repository_no_match_anywhere_returns_empty():
    await connect_db()
    repo = ScenarioRepository()
    try:
        await repo.collection.delete_many({})
        results = await repo.get_active_for_role("a role with no scenarios at all")
        assert results == []
        selected = await repo.select_scenario_for_role("a role with no scenarios at all")
        assert selected is None
    finally:
        await repo.collection.delete_many({})
        await close_db()


@pytest.mark.asyncio
async def test_select_scenario_for_role_is_deterministic():
    await connect_db()
    repo = ScenarioRepository()
    try:
        await repo.collection.delete_many({})
        for sid in ["b_sc", "a_sc"]:
            await repo.create({
                "scenario_id": sid, "role_or_domain": "product manager",
                "topic_name": f"Scenario {sid}", "scenario_context": "ctx",
                "difficulty": "medium", "is_active": True,
            })

        selected_1 = await repo.select_scenario_for_role("product manager")
        selected_2 = await repo.select_scenario_for_role("product manager")

        assert selected_1["scenario_id"] == "a_sc"
        assert selected_1["scenario_id"] == selected_2["scenario_id"]
    finally:
        await repo.collection.delete_many({})
        await close_db()
