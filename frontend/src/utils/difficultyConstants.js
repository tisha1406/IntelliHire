// Mirrors backend/app/ai_interview/core/enums.py DifficultyLevel exactly
// (easy | medium | hard). There is no "adaptive" campaign difficulty band —
// adaptive behavior comes from the interview STRATEGY (e.g. Adaptive Depth)
// and per-topic adaptive difficulty inside the engine, not from a
// company-selectable difficulty_band value. See backend/app/schemas/company.py
// (CampaignCreateRequest/CampaignUpdateRequest.difficulty_band:
// Optional[DifficultyLevel]) for the field this backs.
export const DIFFICULTY_LEVELS = [
    { value: "easy", label: "Easy" },
    { value: "medium", label: "Medium" },
    { value: "hard", label: "Hard" },
];
