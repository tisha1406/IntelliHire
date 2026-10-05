import pytest
from app.ai_interview.question_engine.prompts.resolver import PromptResolver
from app.ai_interview.question_engine.prompts.registry import COMBINATION_REGISTRY
from app.ai_interview.question_engine.schemas import QuestionGenerationRequest
from app.ai_interview.core.enums import InterviewType, TopicDimension, QuestionCategory, DifficultyLevel, QuestionType
from app.ai_interview.question_engine.exceptions import QuestionGenerationError

def create_base_request(
    strategy_id: str,
    interview_type: InterviewType,
    dimension: TopicDimension = None,
    category: QuestionCategory = QuestionCategory.NEW,
    difficulty: DifficultyLevel = DifficultyLevel.MEDIUM
) -> QuestionGenerationRequest:
    return QuestionGenerationRequest(
        session_id="s1",
        turn_number=1,
        topic_id="t1",
        topic_name="Test Topic",
        strategy_id=strategy_id,
        interview_type=interview_type,
        dimension=dimension,
        category=category,
        difficulty=difficulty,
        question_number=1,
        max_questions_for_topic=3,
        selected_question_type=QuestionType.INITIAL,
        allowed_question_types=[QuestionType.INITIAL]
    )

def test_all_16_valid_combinations_resolve():
    for combo in COMBINATION_REGISTRY:
        interview_type = InterviewType(combo.interview_type)
        dimension = TopicDimension.TECHNICAL if combo.dimension_source == "topic" else None
        
        category_str = combo.allowed_categories[0]
        # Map string back to enum
        category = QuestionCategory(category_str)
        
        request = create_base_request(
            strategy_id=combo.strategy_id,
            interview_type=interview_type,
            dimension=dimension,
            category=category
        )
        sys_prompt, user_prompt = PromptResolver.resolve(request)
        assert sys_prompt is not None
        assert combo.combination_id in sys_prompt or "Addendum:" in sys_prompt

def test_invalid_combinations_fail():
    invalid_combos = [
        ("adaptive_depth", InterviewType.RESUME_EXPERIENCE),
        ("adaptive_depth", InterviewType.HR_BEHAVIORAL),
        ("adaptive_depth", InterviewType.SITUATIONAL_CASE),
        ("critical_skills", InterviewType.RESUME_EXPERIENCE),
        ("critical_skills", InterviewType.HR_BEHAVIORAL),
        ("critical_skills", InterviewType.SITUATIONAL_CASE),
        ("critical_skills", InterviewType.MIXED),
        ("gap_verification", InterviewType.RESUME_EXPERIENCE),
        ("gap_verification", InterviewType.HR_BEHAVIORAL),
        ("gap_verification", InterviewType.SITUATIONAL_CASE),
        ("behavioral_adaptive", InterviewType.TECHNICAL),
        ("behavioral_adaptive", InterviewType.RESUME_EXPERIENCE),
        ("behavioral_adaptive", InterviewType.SITUATIONAL_CASE),
        ("behavioral_adaptive", InterviewType.MIXED),
    ]
    
    for strategy_id, interview_type in invalid_combos:
        request = create_base_request(strategy_id, interview_type)
        with pytest.raises(QuestionGenerationError) as exc:
            PromptResolver.resolve(request)
        assert "not a valid combination" in str(exc.value)

def test_mixed_uses_topic_dimension():
    request = create_base_request(
        strategy_id="fixed_coverage",
        interview_type=InterviewType.MIXED,
        dimension=TopicDimension.BEHAVIORAL
    )
    sys_prompt, user_prompt = PromptResolver.resolve(request)
    assert "Dimension: BEHAVIORAL" in sys_prompt
    assert "FC_MIXED" in sys_prompt

def test_mixed_requires_dimension():
    request = create_base_request(
        strategy_id="fixed_coverage",
        interview_type=InterviewType.MIXED,
        dimension=None
    )
    with pytest.raises(QuestionGenerationError) as exc:
        PromptResolver.resolve(request)
    assert "Mixed interview type requires request.dimension to be set" in str(exc.value)

def test_invalid_category_dimension_combinations_fail():
    request = create_base_request(
        strategy_id="adaptive_depth",
        interview_type=InterviewType.MIXED,
        dimension=TopicDimension.BEHAVIORAL,
        category=QuestionCategory.FOLLOWUP_CHALLENGE
    )
    with pytest.raises(QuestionGenerationError) as exc:
        PromptResolver.resolve(request)
    assert "only allowed for technical dimension" in str(exc.value)
    
    request.category = QuestionCategory.CORRECTION
    with pytest.raises(QuestionGenerationError) as exc:
        PromptResolver.resolve(request)
    assert "not allowed for behavioral dimension" in str(exc.value)

def test_invalid_strategy_category_combinations_fail():
    request = create_base_request(
        strategy_id="breadth",
        interview_type=InterviewType.TECHNICAL,
        category=QuestionCategory.FOLLOWUP_DEPTH
    )
    with pytest.raises(QuestionGenerationError) as exc:
        PromptResolver.resolve(request)
    assert "is not allowed for combination 'BS_TECH'" in str(exc.value)

def test_prompt_content_rules():
    request = create_base_request(
        strategy_id="behavioral_adaptive",
        interview_type=InterviewType.HR_BEHAVIORAL,
        category=QuestionCategory.NEW
    )
    request.candidate_claim = "I did this."
    request.interview_evidence = None 
    request.previous_answer = "My previous answer text"
    request.specificity_required = True
    
    sys_prompt, user_prompt = PromptResolver.resolve(request)
    
    assert "A candidate claim is NOT proof; it is just what they said." in sys_prompt
    assert "Interview evidence is read-only backend evidence (do not guess or upgrade it)." in sys_prompt
    assert "A missing resume skill does NOT mean the candidate lacks the skill." in sys_prompt
    assert "My previous answer text" in sys_prompt
    assert "Specificity Required:" in sys_prompt
    assert "True" in sys_prompt
    
def test_scenario_context_reaches_situational():
    request = create_base_request(
        strategy_id="fixed_coverage",
        interview_type=InterviewType.SITUATIONAL_CASE,
        category=QuestionCategory.NEW
    )
    request.scenario_context = "System is down."
    sys_prompt, user_prompt = PromptResolver.resolve(request)
    assert "Scenario Context:" in sys_prompt
    assert "System is down." in sys_prompt

def test_mixed_does_not_expose_composition_arithmetic():
    request = create_base_request(
        strategy_id="fixed_coverage",
        interview_type=InterviewType.MIXED,
        dimension=TopicDimension.TECHNICAL
    )
    sys_prompt, user_prompt = PromptResolver.resolve(request)
    assert "20%" not in sys_prompt
    assert "30%" not in sys_prompt
    assert "composition" not in sys_prompt.lower()
