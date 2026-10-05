import { z } from "zod";

// Mirrors backend/app/ai_interview/schemas/strategy.py StrategyDefinition exactly,
// including the two @model_validator rules (budget ordering, threshold ordering),
// so invalid configurations are caught client-side before hitting the API.
export const strategySchema = z
    .object({
        strategy_id: z
            .string()
            .min(2, "Strategy ID must be at least 2 characters")
            .regex(/^[a-z0-9_]+$/, "Use lowercase letters, numbers, and underscores only (e.g. adaptive_depth)"),
        name: z.string().min(2, "Name must be at least 2 characters"),
        description: z.string().min(1, "Description is required"),
        is_active: z.boolean(),

        applicable_interview_types: z
            .array(z.string())
            .min(1, "Select at least one applicable interview type"),

        budget_mode: z.string().min(1),

        min_questions: z.coerce.number().int("Must be a whole number").min(0, "Must be 0 or greater"),
        target_questions: z.coerce.number().int("Must be a whole number").min(0, "Must be 0 or greater"),
        max_questions: z.coerce.number().int("Must be a whole number").min(0, "Must be 0 or greater"),

        max_questions_per_topic: z.coerce.number().int("Must be a whole number").min(0, "Must be 0 or greater"),
        max_followups_per_topic: z.coerce.number().int("Must be a whole number").min(0, "Must be 0 or greater"),
        critical_topic_max_followups: z.preprocess(
            (val) => (val === "" || val === undefined ? null : val),
            z.coerce.number().int().min(0, "Must be 0 or greater").nullable()
        ),

        strong_threshold: z.coerce.number().min(0, "Must be between 0 and 1").max(1, "Must be between 0 and 1"),
        acceptable_threshold: z.coerce.number().min(0, "Must be between 0 and 1").max(1, "Must be between 0 and 1"),
        weak_threshold: z.coerce.number().min(0, "Must be between 0 and 1").max(1, "Must be between 0 and 1"),

        topic_selection_policy: z.object({
            policy_type: z.string().min(1),
        }),

        difficulty_policy: z.object({
            adapts: z.boolean(),
            scope: z.string().min(1),
            reset_on_switch: z.boolean(),
            step_size: z.coerce.number().int().min(1, "Must be at least 1"),
            band_constrainable: z.boolean(),
        }),

        followup_policy: z.object({
            allowed_categories: z.array(z.string()).default([]),
            max_per_topic: z.coerce.number().int().min(0, "Must be 0 or greater"),
        }),

        gap_policy: z.object({
            enabled: z.boolean(),
            max_share_of_budget: z.coerce.number().min(0, "Must be between 0 and 1").max(1, "Must be between 0 and 1"),
        }),

        completion_policy: z.object({
            allow_early_exit: z.boolean(),
            require_all_critical_covered: z.boolean(),
        }),

        company_override_bounds: z.object({
            target_questions_min_delta: z.coerce.number().int(),
            target_questions_max_delta: z.coerce.number().int(),
            allowed_difficulty_bands: z.array(z.string()).default([]),
        }),
    })
    .superRefine((data, ctx) => {
        if (!(data.min_questions <= data.target_questions && data.target_questions <= data.max_questions)) {
            ctx.addIssue({
                code: z.ZodIssueCode.custom,
                path: ["max_questions"],
                message: "Budgets must satisfy: min_questions ≤ target_questions ≤ max_questions",
            });
        }
        if (
            !(
                data.weak_threshold <= data.acceptable_threshold &&
                data.acceptable_threshold <= data.strong_threshold
            )
        ) {
            ctx.addIssue({
                code: z.ZodIssueCode.custom,
                path: ["strong_threshold"],
                message: "Thresholds must satisfy: weak_threshold ≤ acceptable_threshold ≤ strong_threshold",
            });
        }
    });

// These are blank/neutral starting values for a brand-new strategy, not a
// copy of any existing strategy's configuration. Every field the backend's
// StrategyDefinition declares as *required with no Pydantic default*
// (min/target/max_questions, max_questions_per_topic, max_followups_per_topic,
// the three thresholds) starts at 0 here so a new form never resembles a
// specific published strategy (e.g. Adaptive Depth's real 8/10/12 budget).
// Fields below that DO carry an actual default in
// backend/app/ai_interview/schemas/strategy.py (budget_mode, is_active, and
// every nested policy sub-field) keep that same default, since those are the
// schema's own generic defaults, not a borrowed strategy's numbers.
export const defaultValues = {
    strategy_id: "",
    name: "",
    description: "",
    is_active: true,
    applicable_interview_types: [],
    budget_mode: "fixed",
    min_questions: 0,
    target_questions: 0,
    max_questions: 0,
    max_questions_per_topic: 0,
    max_followups_per_topic: 0,
    critical_topic_max_followups: "",
    strong_threshold: 0,
    acceptable_threshold: 0,
    weak_threshold: 0,
    topic_selection_policy: {
        policy_type: "priority_score",
    },
    difficulty_policy: {
        adapts: true,
        scope: "per_topic",
        reset_on_switch: true,
        step_size: 1,
        band_constrainable: true,
    },
    followup_policy: {
        allowed_categories: [],
        max_per_topic: 2,
    },
    gap_policy: {
        enabled: true,
        max_share_of_budget: 0.4,
    },
    completion_policy: {
        allow_early_exit: true,
        require_all_critical_covered: true,
    },
    company_override_bounds: {
        target_questions_min_delta: 0,
        target_questions_max_delta: 0,
        allowed_difficulty_bands: [],
    },
};
