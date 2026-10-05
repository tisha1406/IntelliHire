"""
D-03 / specs.md R-03 campaign-save-time warning tests.

Mirrors B-04's own test convention (test_campaign_critical_budget_warning.py):
exercises the pure async helper
(`app.api.company.campaigns._situational_scenario_warnings`) directly, using
a real ScenarioRepository backed by the real test MongoDB (connect_db/
close_db, same pattern as tests/integration/test_scenario_repository.py) --
this function's entire job is a single DB existence check, trivial to test
exhaustively without standing up auth/company/campaign HTTP fixtures.
"""
import pytest
import pytest_asyncio

from app.db.mongo import connect_db, close_db
from app.api.company.campaigns import _situational_scenario_warnings
from app.repositories.scenario_repository import ScenarioRepository
from app.ai_interview.schemas.strategy import MixedComposition
from app.ai_interview.core.enums import InterviewType


@pytest_asyncio.fixture
async def clean_scenarios():
    await connect_db()
    repo = ScenarioRepository()
    await repo.collection.delete_many({})
    yield repo
    await repo.collection.delete_many({})
    await close_db()


@pytest.mark.asyncio
async def test_situational_case_with_no_active_scenario_warns(clean_scenarios):
    warnings = await _situational_scenario_warnings(
        InterviewType.SITUATIONAL_CASE, None, "Backend Engineer",
    )
    assert len(warnings) == 1
    assert "Backend Engineer" in warnings[0]


@pytest.mark.asyncio
async def test_situational_case_with_active_scenario_does_not_warn(clean_scenarios):
    await clean_scenarios.create({
        "scenario_id": "s1", "role_or_domain": "backend engineer",
        "topic_name": "T", "scenario_context": "ctx",
        "difficulty": "medium", "is_active": True,
    })
    warnings = await _situational_scenario_warnings(
        InterviewType.SITUATIONAL_CASE, None, "Backend Engineer",
    )
    assert warnings == []


@pytest.mark.asyncio
async def test_mixed_with_zero_situational_weight_never_warns(clean_scenarios):
    comp = MixedComposition(technical=0.6, resume_experience=0.4, hr_behavioral=0.0, situational_case=0.0)
    warnings = await _situational_scenario_warnings(
        InterviewType.MIXED, comp, "Backend Engineer",
    )
    assert warnings == []


@pytest.mark.asyncio
async def test_mixed_with_nonzero_situational_weight_and_no_scenario_warns(clean_scenarios):
    comp = MixedComposition(technical=0.5, resume_experience=0.0, hr_behavioral=0.0, situational_case=0.5)
    warnings = await _situational_scenario_warnings(
        InterviewType.MIXED, comp, "Backend Engineer",
    )
    assert len(warnings) == 1


@pytest.mark.asyncio
async def test_technical_interview_type_never_warns_regardless_of_scenario_availability(clean_scenarios):
    warnings = await _situational_scenario_warnings(
        InterviewType.TECHNICAL, None, "Backend Engineer",
    )
    assert warnings == []


@pytest.mark.asyncio
async def test_no_interview_type_never_warns(clean_scenarios):
    warnings = await _situational_scenario_warnings(None, None, "Backend Engineer")
    assert warnings == []
