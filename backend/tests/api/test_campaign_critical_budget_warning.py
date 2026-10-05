"""
B-04 / R-13 regression tests.

Master rule (specs.md R-13, architecture doc Section 13):
    max_questions_per_topic * count(critical_topics) <= max_questions
Violating this must produce a non-blocking WARNING at campaign save time —
never a hard rejection, and never via the AI interview blueprint-planning
pipeline (that was the incorrect, now-reverted, first attempt at B-04).

These tests exercise the pure helper function directly
(`app.api.company.campaigns._critical_topic_budget_warnings`) rather than the
full HTTP endpoint, since the function contains the entire rule and is trivial
to test exhaustively without standing up auth/company/strategy fixtures.
"""
import pytest

from app.api.company.campaigns import _critical_topic_budget_warnings
from app.ai_interview.schemas.strategy import StrategyDefinition
from app.schemas.company import CampaignRequirement
from app.ai_interview.core.enums import RequirementCriticality


def _strategy(max_questions_per_topic: int, max_questions: int) -> StrategyDefinition:
    return StrategyDefinition(
        strategy_id="test_strategy",
        name="Test Strategy",
        description="A strategy for B-04 testing.",
        applicable_interview_types=["technical"],
        min_questions=1,
        target_questions=max_questions,
        max_questions=max_questions,
        max_questions_per_topic=max_questions_per_topic,
        max_followups_per_topic=2,
        strong_threshold=0.8,
        acceptable_threshold=0.5,
        weak_threshold=0.3,
    )


def _requirement(skill: str, criticality: RequirementCriticality) -> CampaignRequirement:
    return CampaignRequirement(skill=skill, criticality=criticality)


class TestNoWarning:
    def test_exactly_at_the_limit_produces_no_warning(self):
        """specs.md's own valid example: 2 x 5 = 10 <= 12."""
        strategy = _strategy(max_questions_per_topic=2, max_questions=12)
        requirements = [_requirement(f"skill_{i}", RequirementCriticality.CRITICAL) for i in range(5)]
        assert _critical_topic_budget_warnings(strategy, requirements) == []

    def test_product_equal_to_max_questions_is_not_a_warning(self):
        """Boundary: product == max_questions must NOT warn (<=, not <)."""
        strategy = _strategy(max_questions_per_topic=3, max_questions=12)
        requirements = [_requirement(f"skill_{i}", RequirementCriticality.CRITICAL) for i in range(4)]
        assert _critical_topic_budget_warnings(strategy, requirements) == []

    def test_zero_critical_topics_never_warns_regardless_of_max_questions_per_topic(self):
        strategy = _strategy(max_questions_per_topic=100, max_questions=1)
        requirements = [_requirement("skill_a", RequirementCriticality.REQUIRED), _requirement("skill_b", RequirementCriticality.PREFERRED)]
        assert _critical_topic_budget_warnings(strategy, requirements) == []

    def test_no_requirements_never_warns(self):
        strategy = _strategy(max_questions_per_topic=10, max_questions=1)
        assert _critical_topic_budget_warnings(strategy, []) == []
        assert _critical_topic_budget_warnings(strategy, None) == []

    def test_plain_string_requirements_are_never_counted_as_critical(self):
        """Requirements submitted as bare strings carry no criticality info."""
        strategy = _strategy(max_questions_per_topic=10, max_questions=1)
        assert _critical_topic_budget_warnings(strategy, ["Python", "Docker", "Kubernetes"]) == []


class TestWarningProduced:
    def test_specs_md_own_invalid_example_produces_exactly_one_warning(self):
        """specs.md's own invalid example: 4 x 5 = 20 > 12."""
        strategy = _strategy(max_questions_per_topic=4, max_questions=12)
        requirements = [_requirement(f"skill_{i}", RequirementCriticality.CRITICAL) for i in range(5)]
        warnings = _critical_topic_budget_warnings(strategy, requirements)
        assert len(warnings) == 1

    def test_warning_message_names_the_exact_offending_numbers(self):
        """Exact warning representation: all three numbers must be legible in the message."""
        strategy = _strategy(max_questions_per_topic=4, max_questions=12)
        requirements = [_requirement(f"skill_{i}", RequirementCriticality.CRITICAL) for i in range(5)]
        [warning] = _critical_topic_budget_warnings(strategy, requirements)
        assert "4" in warning          # max_questions_per_topic
        assert "5" in warning          # critical requirement count
        assert "20" in warning         # product
        assert "12" in warning         # max_questions
        assert "max_questions_per_topic" in warning
        assert "max_questions" in warning

    def test_only_critical_requirements_count_toward_the_product(self):
        """2 critical x 4 per-topic = 8 > max_questions(6); the 3 non-critical
        requirements must not be counted."""
        strategy = _strategy(max_questions_per_topic=4, max_questions=6)
        requirements = [
            _requirement("critical_1", RequirementCriticality.CRITICAL),
            _requirement("critical_2", RequirementCriticality.CRITICAL),
            _requirement("required_1", RequirementCriticality.REQUIRED),
            _requirement("preferred_1", RequirementCriticality.PREFERRED),
            _requirement("resume_only_1", RequirementCriticality.RESUME_ONLY),
        ]
        warnings = _critical_topic_budget_warnings(strategy, requirements)
        assert len(warnings) == 1
        assert "2" in warnings[0]  # critical count, not 5

    def test_works_with_plain_dicts_as_well_as_pydantic_models(self):
        """update_campaign falls back to the stored Mongo document's
        requirements (plain dicts with string criticality values) when the
        update request doesn't resend requirements."""
        strategy = _strategy(max_questions_per_topic=5, max_questions=5)
        requirements_as_mongo_docs = [
            {"skill": "Kubernetes", "criticality": "critical"},
            {"skill": "Docker", "criticality": "critical"},
        ]
        warnings = _critical_topic_budget_warnings(strategy, requirements_as_mongo_docs)
        assert len(warnings) == 1  # 5 * 2 = 10 > 5


class TestNonBlockingBehavior:
    def test_function_never_raises_even_when_the_rule_is_badly_violated(self):
        """This is the core B-04 requirement: warn, never reject. Proven by
        the function having no raise statement reachable for this input and
        always returning a plain list."""
        strategy = _strategy(max_questions_per_topic=100, max_questions=1)
        requirements = [_requirement(f"skill_{i}", RequirementCriticality.CRITICAL) for i in range(50)]
        result = _critical_topic_budget_warnings(strategy, requirements)  # must not raise
        assert isinstance(result, list)
        assert len(result) == 1


class TestResponseSchemasExposeWarnings:
    def test_campaign_response_accepts_and_defaults_warnings(self):
        from app.schemas.company import CampaignResponse
        resp = CampaignResponse(campaign_id="abc123")
        assert resp.warnings == []
        resp_with_warning = CampaignResponse(campaign_id="abc123", warnings=["some warning"])
        assert resp_with_warning.warnings == ["some warning"]

    def test_campaign_update_response_accepts_and_defaults_warnings(self):
        from app.schemas.company import CampaignUpdateResponse
        resp = CampaignUpdateResponse(updated_fields=["name"])
        assert resp.warnings == []
        resp_with_warning = CampaignUpdateResponse(updated_fields=["strategy_id"], warnings=["some warning"])
        assert resp_with_warning.warnings == ["some warning"]
