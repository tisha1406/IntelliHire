import { describe, it, expect } from "vitest";
import { strategySchema, defaultValues } from "./schema";

function validStrategy(overrides = {}) {
    return {
        ...defaultValues,
        strategy_id: "adaptive_depth",
        name: "Adaptive Depth",
        description: "Depth follows demonstrated performance.",
        applicable_interview_types: ["technical"],
        ...overrides,
    };
}

describe("strategySchema", () => {
    it("accepts a fully valid StrategyDefinition payload", () => {
        const result = strategySchema.safeParse(validStrategy());
        expect(result.success).toBe(true);
    });

    it("rejects a missing strategy_id", () => {
        const result = strategySchema.safeParse(validStrategy({ strategy_id: "" }));
        expect(result.success).toBe(false);
    });

    it("rejects a strategy_id with invalid characters", () => {
        const result = strategySchema.safeParse(validStrategy({ strategy_id: "Adaptive Depth!" }));
        expect(result.success).toBe(false);
    });

    it("rejects an empty applicable_interview_types array", () => {
        const result = strategySchema.safeParse(validStrategy({ applicable_interview_types: [] }));
        expect(result.success).toBe(false);
    });

    it("rejects a budget where min > target", () => {
        const result = strategySchema.safeParse(
            validStrategy({ min_questions: 10, target_questions: 8, max_questions: 12 })
        );
        expect(result.success).toBe(false);
        const issue = result.error.issues.find((i) => i.path.join(".") === "max_questions");
        expect(issue).toBeTruthy();
        expect(issue.message).toMatch(/min_questions.*target_questions.*max_questions/);
    });

    it("rejects a budget where target > max", () => {
        const result = strategySchema.safeParse(
            validStrategy({ min_questions: 8, target_questions: 15, max_questions: 12 })
        );
        expect(result.success).toBe(false);
    });

    it("accepts a budget where min == target == max (Fixed Coverage shape)", () => {
        const result = strategySchema.safeParse(
            validStrategy({ min_questions: 10, target_questions: 10, max_questions: 10 })
        );
        expect(result.success).toBe(true);
    });

    it("rejects thresholds where weak > acceptable", () => {
        const result = strategySchema.safeParse(
            validStrategy({ weak_threshold: 0.6, acceptable_threshold: 0.5, strong_threshold: 0.8 })
        );
        expect(result.success).toBe(false);
        const issue = result.error.issues.find((i) => i.path.join(".") === "strong_threshold");
        expect(issue).toBeTruthy();
    });

    it("rejects thresholds where acceptable > strong", () => {
        const result = strategySchema.safeParse(
            validStrategy({ weak_threshold: 0.3, acceptable_threshold: 0.9, strong_threshold: 0.8 })
        );
        expect(result.success).toBe(false);
    });

    it("rejects a threshold outside the 0..1 range", () => {
        const result = strategySchema.safeParse(validStrategy({ strong_threshold: 1.5 }));
        expect(result.success).toBe(false);
    });

    it("preserves nested policy objects correctly on a valid parse", () => {
        const payload = validStrategy({
            followup_policy: { allowed_categories: ["new", "followup_depth"], max_per_topic: 2 },
            difficulty_policy: { adapts: true, scope: "per_topic", reset_on_switch: true, step_size: 1, band_constrainable: true },
        });
        const result = strategySchema.safeParse(payload);
        expect(result.success).toBe(true);
        expect(result.data.followup_policy.allowed_categories).toEqual(["new", "followup_depth"]);
        expect(result.data.difficulty_policy.scope).toBe("per_topic");
    });

    it("coerces numeric string inputs from form fields", () => {
        const result = strategySchema.safeParse(
            validStrategy({ min_questions: "8", target_questions: "10", max_questions: "12" })
        );
        expect(result.success).toBe(true);
        expect(result.data.min_questions).toBe(8);
    });

    it("treats an empty critical_topic_max_followups as null", () => {
        const result = strategySchema.safeParse(validStrategy({ critical_topic_max_followups: "" }));
        expect(result.success).toBe(true);
        expect(result.data.critical_topic_max_followups).toBeNull();
    });
});
