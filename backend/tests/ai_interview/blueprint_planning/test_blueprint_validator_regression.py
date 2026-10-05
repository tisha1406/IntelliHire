"""
Regression tests proving backend/app/ai_interview/blueprint_planning/
blueprint_validator.py was correctly reverted after an earlier, incorrect
"B-04" attempt added a `_validate_topic_budget_sum` check here (sum of
per-topic TopicBlueprint.question_budget vs total_question_budget, raised as
a hard error). That rule does not match the actual B-04/R-13 requirement
(max_questions_per_topic * critical_topic_count <= max_questions, a
non-blocking warning at campaign-save time — see
tests/api/test_campaign_critical_budget_warning.py) and has been removed.

These tests prove:
1. The method no longer exists on BlueprintValidator.
2. A blueprint whose per-topic budgets sum well beyond total_question_budget
   no longer raises (the incorrect rule is gone).
3. The four original, legitimate checks (budget > 0, min <= total,
   min <= max, no duplicate topic names) are all still intact and unweakened.
"""
import pytest
from app.ai_interview.blueprint_planning.blueprint_validator import BlueprintValidator
from app.ai_interview.blueprint_planning.exceptions import BlueprintValidationError
from app.ai_interview.schemas.blueprint import InterviewBlueprint, TopicBlueprint
from app.ai_interview.core.enums import DifficultyLevel, QuestionType


def _make_topic(name: str, budget: int) -> TopicBlueprint:
    return TopicBlueprint(
        topic_id=f"tid_{name}",
        topic_name=name,
        source="test",
        priority=1,
        mandatory=False,
        initial_difficulty=DifficultyLevel.MEDIUM,
        allowed_question_types=[QuestionType.INITIAL],
        question_budget=budget,
    )


def _make_blueprint(topics, total_budget, min_q=0, max_q=None):
    if max_q is None:
        max_q = total_budget
    return InterviewBlueprint(
        blueprint_version="1.0",
        total_question_budget=total_budget,
        min_questions=min_q,
        max_questions=max_q,
        emergency_max_questions=max_q + 2,
        topics=topics,
    )


def test_the_incorrect_topic_budget_sum_method_was_removed():
    assert not hasattr(BlueprintValidator, "_validate_topic_budget_sum")


def test_topic_budgets_summing_well_beyond_total_no_longer_raises():
    """This exact scenario previously raised under the incorrect B-04 rule
    (10 topics x 2 = 20 > total_budget 10). It must now pass silently — this
    was never a real constraint in the architecture document."""
    topics = [_make_topic(f"topic_{i}", 2) for i in range(10)]
    bp = _make_blueprint(topics=topics, total_budget=10)
    BlueprintValidator.validate(bp)  # must not raise


def test_zero_total_budget_still_raises():
    bp = _make_blueprint(topics=[], total_budget=0, min_q=0, max_q=0)
    with pytest.raises(BlueprintValidationError, match="Total question budget must be"):
        BlueprintValidator.validate(bp)


def test_min_exceeds_total_still_raises():
    bp = _make_blueprint(topics=[], total_budget=5, min_q=10, max_q=5)
    with pytest.raises(BlueprintValidationError, match="Minimum questions cannot exceed total budget"):
        BlueprintValidator.validate(bp)


def test_min_exceeds_max_still_raises():
    bp = _make_blueprint(topics=[], total_budget=20, min_q=15, max_q=10)
    with pytest.raises(BlueprintValidationError, match="Minimum questions cannot exceed maximum questions"):
        BlueprintValidator.validate(bp)


def test_duplicate_topic_still_raises():
    topics = [_make_topic("React", 1), _make_topic("React", 1)]
    bp = _make_blueprint(topics=topics, total_budget=10)
    with pytest.raises(BlueprintValidationError, match="Duplicate topic"):
        BlueprintValidator.validate(bp)


def test_a_normal_valid_blueprint_still_passes():
    topics = [_make_topic("React", 3), _make_topic("Python", 3)]
    bp = _make_blueprint(topics=topics, total_budget=10)
    BlueprintValidator.validate(bp)  # must not raise
