"""
Regression tests: campaign requirement extraction for official session creation.

Root cause: POST /company/campaigns stores requirements as
{"skill": ..., "criticality": ...} dicts, but SessionCreationService passed
campaign["requirements"] straight into JobRequirementContext.required_skills
(List[str]), so create_session() raised a pydantic ValidationError for every
campaign created through the current campaign form. The pre-existing tests
never caught this because they either mock InterviewBlueprintPlanner.plan
entirely or use campaigns with no requirements.

These tests use the REAL planner (no mocking of blueprint planning) and a
campaign stored in the current format.
"""
import pytest
from unittest.mock import AsyncMock, patch

from app.auth.jwt_handler import TokenPayload
from app.ai_interview.transport.services.session_creation_service import (
    SessionCreationService, _extract_required_skill_names,
)
from app.ai_interview.core.enums import RequirementCriticality


@pytest.fixture
def mock_repos():
    return {
        "campaign_repo": AsyncMock(), "mode_repo": AsyncMock(), "resume_repo": AsyncMock(),
        "candidate_repo": AsyncMock(), "session_repo": AsyncMock(),
    }


@pytest.fixture
def service(mock_repos):
    return SessionCreationService(**mock_repos)


@pytest.fixture
def token():
    return TokenPayload(sub="u1", user_id="u1", role="candidate", company_id="comp1",
                        candidate_id="cand1", exp=9999999999, iat=1)


def _wire(mock_repos, requirements):
    mock_repos["campaign_repo"].get_by_id.return_value = {
        "status": "active", "company_id": "comp1", "interview_mode": "m1",
        "name": "Backend Role", "requirements": requirements,
    }
    mock_repos["candidate_repo"].get.return_value = {"campaign_id": "camp1"}
    mock_repos["mode_repo"].get_by_mode_id.return_value = {
        "mode_id": "m1", "version": 1, "name": "mode", "description": "desc",
        "status": "published", "created_at": "2024-01-01T00:00:00Z",
        "settings": {"allowed_question_types": ["initial"]},
    }
    mock_repos["resume_repo"].get_by_candidate.return_value = {"id": "r1"}
    mock_repos["session_repo"].find_active_session.return_value = None


def _saved_session(mock_repos):
    return mock_repos["session_repo"].save.call_args[0][0]


@pytest.mark.asyncio
async def test_current_format_requirements_can_create_an_official_session(service, token, mock_repos):
    _wire(mock_repos, [{"skill": "Python", "criticality": "critical"}])

    result = await service.create_session(token, "camp1")  # previously: ValidationError

    assert result["session_id"]
    assert _saved_session(mock_repos).blueprint.topics


@pytest.mark.asyncio
async def test_required_skills_receives_the_skill_names(service, token, mock_repos):
    _wire(mock_repos, [
        {"skill": "Python", "criticality": "critical"},
        {"skill": "Docker", "criticality": "required"},
        {"skill": "Kubernetes", "criticality": "preferred"},
    ])

    with patch.object(service.planner, "plan", wraps=service.planner.plan) as spy:
        await service.create_session(token, "camp1")

    request = spy.call_args[0][0]
    assert request.job_context.required_skills == ["Python", "Docker", "Kubernetes"]
    names = {t.topic_name for t in _saved_session(mock_repos).blueprint.topics}
    assert {"Python", "Docker", "Kubernetes"} <= names


@pytest.mark.asyncio
async def test_legacy_plain_string_requirements_still_work(service, token, mock_repos):
    """The campaign schema allows Union[str, CampaignRequirement]; plain
    strings were the only shape the old code accepted."""
    _wire(mock_repos, ["Python", "Docker"])

    with patch.object(service.planner, "plan", wraps=service.planner.plan) as spy:
        await service.create_session(token, "camp1")

    assert spy.call_args[0][0].job_context.required_skills == ["Python", "Docker"]


@pytest.mark.asyncio
async def test_mixed_string_and_dict_requirements(service, token, mock_repos):
    _wire(mock_repos, ["Python", {"skill": "Docker", "criticality": "required"}])

    with patch.object(service.planner, "plan", wraps=service.planner.plan) as spy:
        await service.create_session(token, "camp1")

    assert spy.call_args[0][0].job_context.required_skills == ["Python", "Docker"]


@pytest.mark.asyncio
async def test_criticality_remains_available_to_the_planning_pipeline(service, token, mock_repos):
    """The raw requirements list must still reach SessionInitializer so each
    topic keeps its criticality -- extraction must not flatten it away."""
    _wire(mock_repos, [
        {"skill": "Python", "criticality": "critical"},
        {"skill": "Docker", "criticality": "required"},
    ])

    await service.create_session(token, "camp1")

    session = _saved_session(mock_repos)
    name_by_id = {t.topic_id: t.topic_name for t in session.blueprint.topics}
    crit = {name_by_id[tp.topic_id]: tp.criticality for tp in session.topic_progress}
    assert crit["Python"] == RequirementCriticality.CRITICAL
    assert crit["Docker"] == RequirementCriticality.REQUIRED


@pytest.mark.asyncio
async def test_campaign_with_no_requirements_still_creates_a_session(service, token, mock_repos):
    _wire(mock_repos, [])
    mock_repos["resume_repo"].get_by_candidate.return_value = {
        "experience": [{"title": "Backend Developer", "org": "Acme"}],
    }

    result = await service.create_session(token, "camp1")

    assert result["session_id"]


class TestExtractRequiredSkillNames:
    def test_dicts_strings_and_blanks(self):
        reqs = [{"skill": " Python ", "criticality": "critical"}, "Docker", {"skill": ""},
                {"criticality": "required"}, "  "]
        assert _extract_required_skill_names(reqs) == ["Python", "Docker"]

    def test_none_and_empty(self):
        assert _extract_required_skill_names(None) == []
        assert _extract_required_skill_names([]) == []
