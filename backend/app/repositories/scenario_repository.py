from typing import Optional

from app.repositories.base_repository import BaseRepository


class ScenarioRepository(BaseRepository):
    """
    D-03: situational/case scenario bank.

    Scenario documents are seeded data (see scripts/seed_dev_data.py's
    seed_situational_scenarios), never LLM-generated or admin-authored here.
    """

    def __init__(self):
        super().__init__("situational_scenarios")

    async def get_active_for_role(self, role_or_domain: str) -> list[dict]:
        """
        Deterministic retrieval: all active scenarios matching the given
        role/domain (case-insensitive, trimmed), sorted by scenario_id so
        repeated calls with the same inputs always return the same order.

        Falls back to the "general" role/domain bucket when no role-specific
        scenario is active, so a campaign isn't left with no situational
        coverage merely because its exact role string has no dedicated
        scenario -- this is still real seeded data, never a fabricated one.
        """
        role_key = (role_or_domain or "").strip().lower()
        docs = await self.get_many({"role_or_domain": role_key, "is_active": True}, limit=50)
        if not docs and role_key != "general":
            docs = await self.get_many({"role_or_domain": "general", "is_active": True}, limit=50)
        docs.sort(key=lambda d: d["scenario_id"])
        return docs

    async def select_scenario_for_role(self, role_or_domain: str) -> Optional[dict]:
        """
        Deterministic scenario selection: the first active, role-matching
        scenario per get_active_for_role's own deterministic ordering.
        """
        docs = await self.get_active_for_role(role_or_domain)
        return docs[0] if docs else None
