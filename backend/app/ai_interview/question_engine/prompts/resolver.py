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


# Evaluation-signal thresholds used by _summarize_evaluation(). Deterministic
# and fixed -- not learned, not LLM-derived. Scores are the existing 0.0-1.0
# floats already produced by the evaluation pipeline (EvaluationRecord /
# RawEvaluation); nothing here invents a new scale.
_STRONG_THRESHOLD = 0.75
_WEAK_THRESHOLD = 0.45

_COVERAGE_SIGNAL_SUMMARY = {
    "qualitatively_covered": "the topic appears well covered",
    "partially_covered": "coverage of the topic was partial",
    "not_covered": "the topic was not meaningfully covered",
}


def _summarize_evaluation(evaluation) -> str:
    """
    Deterministic, non-LLM summary of the previous answer's evaluation
    signals, replacing the previous raw Python str(dict) rendering (which
    leaked implementation-oriented field names and dict syntax straight into
    the prompt).

    Built only from the fields QuestionRequestBuilder already places on this
    dict (see question_request_builder.py): score, correctness, coverage,
    confidence, qualitative_coverage_signal, evidence_quality,
    followup_recommended. In the current evaluation pipeline
    (EvaluationApplicator), only `score` (overall_score) and
    `qualitative_coverage_signal` are ever actually populated -- the others
    stay None/absent today. This function still safely incorporates them
    when present (e.g. if the evaluator is extended later) but never assumes
    they are -- every field is optional and simply contributes nothing to
    the summary when missing. No conclusion is stated unless an existing
    value genuinely supports it; no new evaluation fields are invented.

    followup_recommended is deliberately NEVER rendered here: the
    deterministic engine (not this evaluation hint) already decided the
    question category upstream, and surfacing this flag risks it reading as
    an instruction to the model rather than context.
    """
    if not evaluation or not isinstance(evaluation, dict):
        return "NOT_PROVIDED"

    parts = []

    score = evaluation.get("score")
    if isinstance(score, (int, float)):
        if score >= _STRONG_THRESHOLD:
            parts.append("the answer was strong")
        elif score < _WEAK_THRESHOLD:
            parts.append("the answer was weak")
        else:
            parts.append("the answer was adequate")

    coverage_signal = evaluation.get("qualitative_coverage_signal")
    if coverage_signal in _COVERAGE_SIGNAL_SUMMARY:
        parts.append(_COVERAGE_SIGNAL_SUMMARY[coverage_signal])

    correctness = evaluation.get("correctness")
    if isinstance(correctness, (int, float)):
        if correctness >= _STRONG_THRESHOLD:
            parts.append("it was technically correct")
        elif correctness < _WEAK_THRESHOLD:
            parts.append("it contained technical inaccuracies")

    confidence = evaluation.get("confidence")
    if isinstance(confidence, (int, float)) and confidence < _WEAK_THRESHOLD:
        parts.append("the answer seemed vague or uncertain")

    evidence_quality = evaluation.get("evidence_quality")
    if isinstance(evidence_quality, str):
        quality = evidence_quality.strip().lower()
        if quality in ("weak", "low", "insufficient"):
            parts.append("it lacked concrete evidence")
        elif quality in ("strong", "high"):
            parts.append("it included concrete evidence")

    if not parts:
        return "NOT_PROVIDED"

    summary = "; ".join(parts) + "."
    return summary[0].upper() + summary[1:]


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


def _experience_and_project_context(request: QuestionGenerationRequest) -> str:
    """Task 7 (Issue B): deterministic, bounded resume/project context for
    the non-technical dimensions (RESUME, BEHAVIORAL, SITUATIONAL), built
    only from the request's existing relevant_experience / relevant_projects
    (already selected for the topic by QuestionRequestBuilder).

    Before this fix, RESUME got only a flat ", ".join(relevant_experience)
    string (projects silently dropped despite the Resume dimension being
    project-centric per the strategy docs), and BEHAVIORAL/SITUATIONAL got
    nothing at all -- ENV_BEHAVIORAL/ENV_SITUATIONAL had no
    {relevant_resume_context} placeholder, so the value computed here was
    silently discarded by PromptCompiler's tolerance of unused kwargs.

    Skills are deliberately excluded (that's a technical-specific concept
    handled by _technical_resume_context); this never fabricates and returns
    "NOT_PROVIDED" when nothing is relevant, matching the technical helper's
    contract."""
    sections = []
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
            # dimension gets bounded experience/projects (Task 7, Issue B --
            # see _experience_and_project_context's docstring for what this
            # replaced).
            relevant_resume_context=(
                _technical_resume_context(request) if effective_dimension == "technical"
                else _experience_and_project_context(request)
            ),
            # The candidate's answer is candidate-controlled text now reaching
            # the prompt: strip angle brackets so it cannot close the
            # <previous_answer_data> wrapper PromptCompiler puts around it.
            previous_answer=_strip_markup(request.previous_answer) if request.previous_answer else "NOT_PROVIDED",
            previous_evaluation=_summarize_evaluation(request.previous_evaluation),
            candidate_claim=request.candidate_claim or "NOT_PROVIDED",
            interview_evidence=request.interview_evidence.value if request.interview_evidence else "NOT_PROVIDED",
            specificity_required=request.specificity_required.value if hasattr(request.specificity_required, 'value') else (str(request.specificity_required) if request.specificity_required is not None else "NOT_PROVIDED"),
            scenario_context=request.scenario_context or "NOT_PROVIDED"
        )

        # Append context that is already computed upstream (on the request
        # object) but has no placeholder in any ENVELOPE_BLOCKS template.
        # Appended here, after compilation, in the same "Label: value" line
        # convention the envelope templates already use, rather than editing
        # the template strings themselves (out of scope for this task).
        #
        # previous_question_for_followup: lets a follow-up naturally connect
        # to the question that was actually asked, not just the answer given.
        rendered_envelope += (
            "\nPrevious Question: "
            + (_strip_markup(request.previous_question_for_followup)
               if request.previous_question_for_followup else "NOT_PROVIDED")
        )

        # question_number / max_questions_for_topic: a soft, informational
        # pacing signal only. Deliberately worded as context, not an
        # instruction -- the deterministic engine (QuestionTurnPlanner /
        # CompletionEngine) remains solely responsible for deciding when a
        # topic or the interview is complete, how many questions are asked,
        # or what category/difficulty comes next. This line must never be
        # read by the model as permission or a requirement to count
        # questions, finish the topic, or change its behavior accordingly.
        if request.question_number is not None and request.max_questions_for_topic is not None:
            rendered_envelope += (
                f"\nTopic Progress (informational only, not a decision for you to make): "
                f"question {request.question_number} of up to {request.max_questions_for_topic} "
                f"currently planned for this topic."
            )

        # Task 7 (Issue A): requirement_criticality was already computed by
        # QuestionTurnPlanner/QuestionRequestBuilder and present on the
        # request, but never rendered anywhere -- confirmed by inspection of
        # resolver.py before this change. It is deliberately surfaced ONLY
        # for the gap_verification category (the one place it is actually
        # relevant to how the question should be phrased, per the audit);
        # injecting it into every technical question would be irrelevant
        # noise for categories that have nothing to do with a requirement
        # gap. This is read-only context -- the backend already decided the
        # requirement and its criticality; the model never decides either.
        if category == "gap_verification" and request.requirement_criticality is not None:
            rendered_envelope += (
                f"\nRequirement Criticality: {request.requirement_criticality.value}"
            )

        rendered_category = PromptCompiler.compile(
            category_block,
            topic_name=request.topic_name or "NOT_PROVIDED"
        )

        # 6. Assemble Final System Prompt -- stable instructions only.
        # Atomic Task 3: the dynamic per-turn envelope no longer lives here;
        # it moves to the user message (below). Every other block, order, and
        # piece of text is unchanged from before this task.
        system_parts = [
            common_block,
            strategy_block,
            rendered_dimension,
            rendered_category,
            addendum_block,
            output_contract
        ]

        system_prompt = "\n\n".join(system_parts)

        # 7. User Prompt -- the generation trigger plus the dynamic interview
        # data envelope for this turn (topic, difficulty, resume context,
        # previous question/answer/evaluation, topic progress, etc.). The
        # envelope itself is produced by the exact same rendering above
        # (PromptCompiler.compile() + the Task 2 appended lines) -- only
        # where it is placed has changed, not how it is built or sanitized.
        user_prompt = (
            "Generate exactly one candidate-facing interview question now. Return only the question text.\n\n"
            "Here is the context for this interview turn:\n"
            + rendered_envelope
        )

        return system_prompt, user_prompt
