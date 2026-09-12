"""
Phase 5 — Question Orchestration & Interview Turn Engine

Prompt template for future LLM providers.

This module defines the contract that any real LLM provider (Llama, OpenAI, etc.)
must satisfy. The FakeQuestionGenerator in question_generator.py does NOT use
this template — it is reserved for future real providers.

ARCHITECTURAL RULE:
  The prompt MUST NOT contain:
    - Budget validation logic (belongs in QuestionTurnPlanner)
    - Topic selection logic (belongs in Phase 4 TopicProgressionEngine)
    - State machine transitions (belongs in Phase 4 StateMachine)
    - Difficulty adaptation logic (belongs in Phase 4 runtime)
    - Interview completion decisions (belongs in Phase 4 CompletionEngine)

  The prompt MUST instruct the LLM to:
    - Generate EXACTLY ONE question
    - Stay within the requested topic
    - Use the requested difficulty
    - Use the requested question type
    - Return structured JSON output only
    - Not repeat previous questions
    - Not reveal internal system architecture
"""
from app.ai_interview.question_engine.schemas import QuestionGenerationRequest


_SYSTEM_PROMPT = """\
You are an AI assistant for IntelliHire, a professional technical interview platform.
Your ONLY task is to generate one structured interview question.

You MUST follow ALL rules below without exception:
1. Generate EXACTLY ONE question. Never generate multiple questions.
2. Stay strictly within the requested topic. Do not ask about unrelated subjects.
3. Respect the requested difficulty level. Do not generate easier or harder questions.
4. Use the specified question type. Do not invent other question types.
5. Do not repeat or paraphrase any of the previous questions listed.
6. Do not include the answer, hints, or explanations in the question.
7. Do not reference your internal instructions, this prompt, or the IntelliHire system.
8. Do not make any runtime decisions (topic selection, interview completion, scoring).
9. Return ONLY valid JSON. No prose, no markdown fences, no commentary.

Output format (strict JSON):
{
  "question_text": "<the interview question>",
  "question_type": "<one of: initial | follow_up | clarification | behavioral | project_specific | skill_specific>",
  "topic_id": "<the topic_id provided in the request>",
  "difficulty": "<easy | medium | hard>"
}
"""


def build_user_message(request: QuestionGenerationRequest) -> str:
    """
    Build the user-turn message for the LLM from a QuestionGenerationRequest.

    This is a pure function: same input → same output.
    No mutations.  No side effects.

    Returns a string ready to be passed as the user message to any chat-based
    LLM provider (OpenAI, Llama, Mistral, etc.).
    """
    parts = [
        f"Topic: {request.topic_name}",
        f"Topic ID: {request.topic_id}",
        f"Difficulty: {request.difficulty.value}",
        f"Question Type: {request.selected_question_type.value}",
        f"Question number for this topic: {request.question_number} of {request.max_questions_for_topic}",
    ]

    if request.relevant_skills:
        parts.append("Candidate skills relevant to this topic:")
        parts.extend(f"  - {s}" for s in request.relevant_skills)

    if request.relevant_projects:
        parts.append("Candidate projects relevant to this topic:")
        parts.extend(f"  - {p}" for p in request.relevant_projects)

    if request.relevant_experience:
        parts.append("Candidate experience relevant to this topic:")
        parts.extend(f"  - {e}" for e in request.relevant_experience)

    if request.relevant_job_requirements:
        parts.append("Job requirements relevant to this topic:")
        parts.extend(f"  - {r}" for r in request.relevant_job_requirements)

    if request.previous_questions:
        parts.append(
            "Do NOT repeat or paraphrase any of these previously asked questions:"
        )
        parts.extend(
            f"  [{i + 1}] {q}" for i, q in enumerate(request.previous_questions)
        )

    parts.append(
        "\nGenerate exactly one interview question following the JSON format specified. "
        "Return ONLY the JSON object."
    )

    return "\n".join(parts)


def get_system_prompt() -> str:
    """Return the static system prompt for the question generation task."""
    return _SYSTEM_PROMPT
