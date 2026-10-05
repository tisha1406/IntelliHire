# backend/app/ai_interview/question_engine/prompts/resolver.py

from app.ai_interview.question_engine.schemas import QuestionGenerationRequest
from app.ai_interview.question_engine.prompts import blocks, registry
from app.ai_interview.question_engine.exceptions import QuestionGenerationError
from app.ai_interview.llm_infrastructure.prompts import PromptCompiler

# Bounds for the structured resume context shown to a technical question.
# Items are already topic-relevant (QuestionRequestBuilder selects them by
# deterministic substring match against the topic); these only cap volume.
MAX_CONTEXT_SKILLS = 5
MAX_CONTEXT_EXPERIENCE = 3
MAX_CONTEXT_PROJECTS = 3
MAX_CONTEXT_ITEM_CHARS = 300


def _clean(text: str) -> str:
    """Single-line, bounded, and unable to close the <..._data> wrapper that
    PromptCompiler puts around every value."""
    text = " ".join(str(text).replace("<", "").replace(">", "").split())
    if len(text) > MAX_CONTEXT_ITEM_CHARS:
        text = text[: MAX_CONTEXT_ITEM_CHARS - 3].rstrip() + "..."
    return text


def _strip_markup(text: str) -> str:
    return str(text).replace("<", "").replace(">", "")


def _technical_resume_context(request: QuestionGenerationRequest) -> str:
    """Deterministic, bounded, structured resume context for a TECHNICAL
    question, built only from the request's existing relevant_skills /
    relevant_experience / relevant_projects (already selected for the topic).
    Returns "NOT_PROVIDED" when nothing is relevant -- never fabricates."""
    sections = []
    skills = [_clean(s) for s in request.relevant_skills[:MAX_CONTEXT_SKILLS] if str(s).strip()]
    if skills:
        sections.append("Relevant Skills: " + ", ".join(skills))
    experience = [_clean(e) for e in request.relevant_experience[:MAX_CONTEXT_EXPERIENCE] if str(e).strip()]
    if experience:
        sections.append("Relevant Experience:\n" + "\n".join(f"- {e}" for e in experience))
    projects = [_clean(p) for p in request.relevant_projects[:MAX_CONTEXT_PROJECTS] if str(p).strip()]
    if projects:
        sections.append("Relevant Projects:\n" + "\n".join(f"- {p}" for p in projects))
    return "\n".join(sections) if sections else "NOT_PROVIDED"


class PromptResolver:
    """
    PromptResolver's only job is prompt resolution.
    It does NOT make interview decisions (e.g. topic, category, difficulty, follow-up, etc.).
    It validates that the decisions made by the deterministic backend are valid combinations
    and constructs the final prompt from the production library.
    """
    
    @staticmethod
    def resolve(request: QuestionGenerationRequest) -> tuple[str, str]:
        """
        Returns (system_prompt, user_prompt)
        """
        if not request.strategy_id or not request.interview_type:
            raise QuestionGenerationError("PromptResolver requires strategy_id and interview_type from the backend.")
            
        strategy_id = request.strategy_id
        interview_type = request.interview_type.value
        
        # 1. Determine and validate combination
        combo = registry.get_combination(strategy_id, interview_type)
        if not combo:
            raise QuestionGenerationError(
                f"Invalid configuration: Strategy '{strategy_id}' with InterviewType '{interview_type}' is not a valid combination."
            )
            
        category = request.category.value if request.category else "new"
        if category not in combo.allowed_categories:
            raise QuestionGenerationError(
                f"Invalid configuration: Category '{category}' is not allowed for combination '{combo.combination_id}'."
            )
            
        # 2. Determine effective dimension
        if combo.dimension_source == "interview_type":
            effective_dimension = registry.map_interview_type_to_dimension(interview_type)
        else:
            # Mixed interview type: use topic's dimension
            if not request.dimension:
                raise QuestionGenerationError("Mixed interview type requires request.dimension to be set by the backend.")
            effective_dimension = request.dimension.value

        # 3. Category x Dimension Restrictions
        if category == "followup_challenge" and effective_dimension != "technical":
            raise QuestionGenerationError("TECHNICAL_CHALLENGE category is only allowed for technical dimension.")
        if category == "correction" and effective_dimension == "behavioral":
            raise QuestionGenerationError("CORRECTION category is not allowed for behavioral dimension.")
        if category == "gap_verification" and effective_dimension != "technical":
            raise QuestionGenerationError("GAP_VERIFICATION category is only allowed for technical dimension.")

        # 4. Load blocks
        common_block = blocks.COMMON_BLOCK
        strategy_block = blocks.STRATEGY_BLOCKS[strategy_id]
        dimension_block = blocks.DIMENSION_BLOCKS[effective_dimension]
        envelope_block = blocks.ENVELOPE_BLOCKS[effective_dimension]
        
        try:
            category_block = blocks.CATEGORY_BLOCKS[category][effective_dimension]
        except KeyError:
            raise QuestionGenerationError(f"Category '{category}' is not supported for dimension '{effective_dimension}'.")
            
        addendum_block = blocks.COMBINATION_ADDENDA[combo.combination_id]
        output_contract = blocks.OUTPUT_CONTRACT

        # 5. Render placeholders using the PromptCompiler
        rendered_dimension = PromptCompiler.compile(
            dimension_block,
            difficulty=request.difficulty.value if request.difficulty else "NOT_PROVIDED"
        )
        
        rendered_envelope = PromptCompiler.compile(
            envelope_block,
            topic_name=request.topic_name or "NOT_PROVIDED",
            difficulty=request.difficulty.value if request.difficulty else "NOT_PROVIDED",
            campaign_requirement=request.campaign_requirement or "NOT_PROVIDED",
            resume_evidence=request.resume_evidence.value if request.resume_evidence else "NOT_PROVIDED",
            # Technical gets bounded skills/experience/projects; every other
            # dimension keeps its existing experience-only behaviour.
            relevant_resume_context=(
                _technical_resume_context(request) if effective_dimension == "technical"
                else (", ".join(request.relevant_experience) if request.relevant_experience else "NOT_PROVIDED")
            ),
            # The candidate's answer is candidate-controlled text now reaching
            # the prompt: strip angle brackets so it cannot close the
            # <previous_answer_data> wrapper PromptCompiler puts around it.
            previous_answer=_strip_markup(request.previous_answer) if request.previous_answer else "NOT_PROVIDED",
            previous_evaluation=str(request.previous_evaluation) if request.previous_evaluation else "NOT_PROVIDED",
            candidate_claim=request.candidate_claim or "NOT_PROVIDED",
            interview_evidence=request.interview_evidence.value if request.interview_evidence else "NOT_PROVIDED",
            specificity_required=request.specificity_required.value if hasattr(request.specificity_required, 'value') else (str(request.specificity_required) if request.specificity_required is not None else "NOT_PROVIDED"),
            scenario_context=request.scenario_context or "NOT_PROVIDED"
        )
        
        rendered_category = PromptCompiler.compile(
            category_block,
            topic_name=request.topic_name or "NOT_PROVIDED"
        )

        # 6. Assemble Final System Prompt
        system_parts = [
            common_block,
            strategy_block,
            rendered_dimension,
            rendered_envelope,
            rendered_category,
            addendum_block,
            output_contract
        ]
        
        system_prompt = "\n\n".join(system_parts)
        
        # 7. User Prompt
        user_prompt = "Generate exactly one candidate-facing interview question now. Return only the question text."
        
        return system_prompt, user_prompt
