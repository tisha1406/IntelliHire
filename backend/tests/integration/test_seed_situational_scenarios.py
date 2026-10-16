"""
Task 8: integration tests for the situational/case scenario bank seed data.

Follows the same real-MongoDB convention as test_seed_interview_modes.py:
clear the collection, run the seed, verify schema conformity + idempotency,
and leave the seeded data in place afterward (this collection is meant to
stay populated for real dev/local use, same as interview modes).
"""
import re

import pytest

from app.db.mongo import connect_db, close_db
from app.repositories.scenario_repository import ScenarioRepository
from app.ai_interview.blueprint_planning.scenario_schemas import Scenario
from scripts.seed_dev_data import seed_situational_scenarios

# Phrases that would mean the scenario text is instructing the LLM rather
# than describing the workplace situation itself (Task 8, Section 3).
_FORBIDDEN_INSTRUCTION_PHRASES = [
    "ask the candidate",
    "you should",
    "evaluate",
    "respond with",
    "the model must",
]


@pytest.mark.asyncio
async def test_seed_situational_scenarios():
    await connect_db()
    try:
        repo = ScenarioRepository()

        # 1. Clear collection first to ensure clean state.
        await repo.collection.delete_many({})

        # 2. Run seed.
        await seed_situational_scenarios()

        # 3. The scenario bank is no longer empty.
        docs = await repo.get_many({}, limit=100)
        assert len(docs) == 5, f"Expected 5 seeded scenarios, got {len(docs)}"

        # 4. Every seeded scenario satisfies the existing Scenario schema and
        # has its required fields populated (non-empty, not a placeholder).
        role_domains = set()
        difficulties = set()
        for doc in docs:
            scenario = Scenario.model_validate(doc)  # raises if schema is violated
            assert scenario.scenario_id.strip()
            assert scenario.role_or_domain.strip()
            assert scenario.topic_name.strip()
            assert len(scenario.scenario_context.strip()) >= 40  # a real situation, not a stub
            assert scenario.is_active is True
            role_domains.add(scenario.role_or_domain)
            difficulties.add(scenario.difficulty)

        # 5. Sufficiently varied: distinct roles/domains and more than one
        # difficulty level, not ten reworded copies of the same scenario.
        assert len(role_domains) == 5
        assert "general" in role_domains  # the fallback bucket exists
        assert len(difficulties) >= 2

        # 6. Distinct topic_name/scenario_context per scenario (no duplicates).
        topic_names = [d["topic_name"] for d in docs]
        contexts = [d["scenario_context"] for d in docs]
        assert len(set(topic_names)) == len(topic_names)
        assert len(set(contexts)) == len(contexts)

        # 7. No scenario contains prompt-instruction text -- it must describe
        # the workplace situation, never instruct the model.
        for doc in docs:
            context_lower = doc["scenario_context"].lower()
            for phrase in _FORBIDDEN_INSTRUCTION_PHRASES:
                assert phrase not in context_lower, (
                    f"{doc['scenario_id']} scenario_context contains forbidden "
                    f"instruction phrase {phrase!r}"
                )

        # 8. Run seed again to verify idempotency (should not duplicate).
        await seed_situational_scenarios()
        docs_after_second_seed = await repo.get_many({}, limit=100)
        assert len(docs_after_second_seed) == 5, "Idempotency failed: duplicated documents created."
    finally:
        await close_db()


@pytest.mark.asyncio
async def test_seeded_scenarios_are_retrievable_through_the_existing_deterministic_path():
    """Situational/Case planning retrieves scenarios through
    ScenarioRepository.select_scenario_for_role -- confirm the seeded data is
    actually reachable through that real, existing path (not just present in
    the collection)."""
    await connect_db()
    try:
        repo = ScenarioRepository()
        await repo.collection.delete_many({})
        await seed_situational_scenarios()

        backend = await repo.select_scenario_for_role("Backend Engineer")
        assert backend is not None
        assert backend["scenario_id"] == "sit_backend_001"

        # Falls back to the general bucket for a role with no dedicated scenario.
        unknown_role = await repo.select_scenario_for_role("underwater basket weaver")
        assert unknown_role is not None
        assert unknown_role["scenario_id"] == "sit_general_001"
    finally:
        await close_db()
