/**
 * @vitest-environment jsdom
 */
import React from "react";
import { render, screen, fireEvent, waitFor, cleanup } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { vi, describe, it, expect, beforeEach, afterEach } from "vitest";

const mockNavigate = vi.fn();
vi.mock("react-router-dom", async () => {
    const actual = await vi.importActual("react-router-dom");
    return { ...actual, useNavigate: () => mockNavigate };
});

const mockGetStrategy = vi.fn();
const mockCreateStrategy = vi.fn();
const mockCreateStrategyVersion = vi.fn();
vi.mock("../../../api/strategies", () => ({
    StrategiesAPI: {
        getStrategy: (...args) => mockGetStrategy(...args),
        createStrategy: (...args) => mockCreateStrategy(...args),
        createStrategyVersion: (...args) => mockCreateStrategyVersion(...args),
    },
}));

import StrategyForm from "./index.jsx";

function renderForm(props = {}) {
    return render(
        <MemoryRouter>
            <StrategyForm {...props} />
        </MemoryRouter>
    );
}

describe("StrategyForm", () => {
    beforeEach(() => {
        mockNavigate.mockReset();
        mockGetStrategy.mockReset();
        mockCreateStrategy.mockReset();
        mockCreateStrategyVersion.mockReset();

        // jsdom has no matchMedia implementation; react-hot-toast's Toaster
        // queries it on mount to detect a reduced-motion/dark-mode preference.
        if (!window.matchMedia) {
            window.matchMedia = () => ({
                matches: false,
                media: "",
                onchange: null,
                addListener: () => {},
                removeListener: () => {},
                addEventListener: () => {},
                removeEventListener: () => {},
                dispatchEvent: () => false,
            });
        }
    });

    afterEach(() => {
        cleanup();
    });

    it("renders the create form with no prefilled data and an enabled Create button", () => {
        renderForm();
        expect(screen.getByText("New Interview Strategy")).toBeTruthy();
        expect(screen.getByPlaceholderText("e.g. my_custom_strategy").value).toBe("");
        const createBtn = screen.getByRole("button", { name: /create strategy/i });
        expect(createBtn.disabled).toBe(false);
    });

    it("does NOT initialize the New Strategy form with the seeded Adaptive Depth strategy's values", () => {
        // Regression test for the E-02 UX correction: a blank New Strategy
        // form must never resemble a specific existing strategy (strategy_id,
        // name, description, or its real 8/10/12 budget and 0.8/0.5/0.3
        // thresholds), whether that previously came from hardcoded form
        // defaults or from placeholder text that merely looked like real data.
        renderForm();

        expect(screen.getByPlaceholderText("e.g. my_custom_strategy").value).toBe("");
        expect(screen.getByPlaceholderText("e.g. My Custom Strategy").value).toBe("");
        expect(screen.getByPlaceholderText(/describe how this strategy should/i).value).toBe("");

        // No text in the rendered form should literally be "adaptive_depth" or
        // "Adaptive Depth" as an actual field VALUE (placeholders are fine,
        // they are not values — verified above that the fields are empty).
        expect(screen.queryByDisplayValue("adaptive_depth")).toBeNull();
        expect(screen.queryByDisplayValue("Adaptive Depth")).toBeNull();

        // The required-with-no-backend-default numeric fields (budget +
        // thresholds) must start neutral at 0, not at Adaptive Depth's
        // published spec values (min 8 / target 10 / max 12, thresholds
        // 0.8/0.5/0.3).
        const numberInputs = screen.getAllByRole("spinbutton");
        const numericValues = numberInputs.map((el) => el.value);
        expect(numericValues).not.toContain("8");
        expect(numericValues).not.toContain("10");
        expect(numericValues).not.toContain("12");
        expect(numericValues).not.toContain("0.8");
        expect(numericValues).not.toContain("0.5");
        expect(numericValues).not.toContain("0.3");

        // No interview type / follow-up category / difficulty band should be
        // pre-selected (Adaptive Depth's real topics and categories would
        // otherwise start checked). Other boolean policy toggles (e.g.
        // is_active, difficulty_policy.adapts) legitimately default to true
        // per StrategyDefinition's own Pydantic defaults and are intentionally
        // not asserted here — only the option-group checkboxes are checked.
        expect(screen.getByRole("checkbox", { name: "Technical" }).checked).toBe(false);
        expect(screen.getByRole("checkbox", { name: "Mixed" }).checked).toBe(false);
        expect(screen.getByRole("checkbox", { name: "New" }).checked).toBe(false);
        expect(screen.getByRole("checkbox", { name: "Easy" }).checked).toBe(false);
    });

    it("shows required-field validation errors and does not call the API on an empty submit", async () => {
        renderForm();
        fireEvent.click(screen.getByRole("button", { name: /create strategy/i }));

        await waitFor(() => {
            expect(screen.getAllByText(/at least 2 characters/i).length).toBeGreaterThan(0);
        });
        expect(mockCreateStrategy).not.toHaveBeenCalled();
    });

    it("shows a budget-ordering validation error when max < target", async () => {
        renderForm();

        fireEvent.change(screen.getByPlaceholderText("e.g. my_custom_strategy"), { target: { value: "test_strategy" } });
        fireEvent.change(screen.getByPlaceholderText("e.g. My Custom Strategy"), { target: { value: "Test Strategy" } });
        fireEvent.change(
            screen.getByPlaceholderText(/describe how this strategy should/i),
            { target: { value: "A test strategy description." } }
        );
        // checkbox 0 = "Active", checkbox 1 = first interview type ("Technical")
        fireEvent.click(screen.getAllByRole("checkbox")[1]);

        const numberInputs = screen.getAllByRole("spinbutton");
        // min/target/max are the first three number inputs rendered in the Budget section
        fireEvent.change(numberInputs[0], { target: { value: "8" } }); // min
        fireEvent.change(numberInputs[1], { target: { value: "15" } }); // target
        fireEvent.change(numberInputs[2], { target: { value: "12" } }); // max

        fireEvent.click(screen.getByRole("button", { name: /create strategy/i }));

        await waitFor(() => {
            expect(screen.getAllByText(/min_questions.*target_questions.*max_questions/i).length).toBeGreaterThan(0);
        });
        expect(mockCreateStrategy).not.toHaveBeenCalled();
    });

    it("submits a valid create form and navigates to the new strategy's detail page", async () => {
        mockCreateStrategy.mockResolvedValue({ strategy_id: "test_strategy" });
        renderForm();

        fireEvent.change(screen.getByPlaceholderText("e.g. my_custom_strategy"), { target: { value: "test_strategy" } });
        fireEvent.change(screen.getByPlaceholderText("e.g. My Custom Strategy"), { target: { value: "Test Strategy" } });
        fireEvent.change(
            screen.getByPlaceholderText(/describe how this strategy should/i),
            { target: { value: "A test strategy description." } }
        );
        fireEvent.click(screen.getAllByRole("checkbox")[1]); // first interview type option

        fireEvent.click(screen.getByRole("button", { name: /create strategy/i }));

        await waitFor(() => {
            expect(mockCreateStrategy).toHaveBeenCalledTimes(1);
        });
        const payload = mockCreateStrategy.mock.calls[0][0];
        expect(payload.strategy_id).toBe("test_strategy");
        expect(payload.name).toBe("Test Strategy");
        expect(payload.applicable_interview_types.length).toBeGreaterThan(0);

        await waitFor(() => {
            expect(mockNavigate).toHaveBeenCalledWith("/admin/strategies/test_strategy");
        });
    });

    it("shows the backend error message when the API call fails (e.g. duplicate strategy_id)", async () => {
        mockCreateStrategy.mockRejectedValue(new Error("Strategy already exists. Use the versions endpoint to create a new version."));
        renderForm();

        fireEvent.change(screen.getByPlaceholderText("e.g. my_custom_strategy"), { target: { value: "adaptive_depth" } });
        fireEvent.change(screen.getByPlaceholderText("e.g. My Custom Strategy"), { target: { value: "Adaptive Depth" } });
        fireEvent.change(
            screen.getByPlaceholderText(/describe how this strategy should/i),
            { target: { value: "A test strategy description." } }
        );
        fireEvent.click(screen.getAllByRole("checkbox")[1]);

        fireEvent.click(screen.getByRole("button", { name: /create strategy/i }));

        await waitFor(() => {
            expect(screen.getAllByText(/strategy already exists/i).length).toBeGreaterThan(0);
        });
        expect(mockNavigate).not.toHaveBeenCalled();
    });

    const existingAdaptiveDepth = {
        strategy_id: "adaptive_depth",
        name: "Adaptive Depth",
        description: "Existing description",
        is_active: true,
        applicable_interview_types: ["technical", "mixed"],
        budget_mode: "fixed",
        min_questions: 8,
        target_questions: 10,
        max_questions: 12,
        max_questions_per_topic: 3,
        max_followups_per_topic: 2,
        critical_topic_max_followups: null,
        strong_threshold: 0.8,
        acceptable_threshold: 0.5,
        weak_threshold: 0.3,
        topic_selection_policy: { policy_type: "priority_score" },
        difficulty_policy: { adapts: true, scope: "per_topic", reset_on_switch: true, step_size: 1, band_constrainable: true },
        followup_policy: { allowed_categories: ["new"], max_per_topic: 2 },
        gap_policy: { enabled: true, max_share_of_budget: 0.4 },
        completion_policy: { allow_early_exit: true, require_all_critical_covered: true },
        company_override_bounds: { target_questions_min_delta: 0, target_questions_max_delta: 0, allowed_difficulty_bands: [] },
    };

    it("loads existing strategy data in edit mode and locks strategy_id (E-01/E-02 behavior unchanged)", async () => {
        mockGetStrategy.mockResolvedValue(existingAdaptiveDepth);

        renderForm({ strategyId: "adaptive_depth" });

        await waitFor(() => {
            expect(mockGetStrategy).toHaveBeenCalledWith("adaptive_depth");
        });

        const strategyIdInput = await screen.findByDisplayValue("adaptive_depth");
        expect(strategyIdInput.disabled).toBe(true);
        expect(screen.getByDisplayValue("Adaptive Depth")).toBeTruthy();
        expect(screen.getByDisplayValue("Existing description")).toBeTruthy();
    });

    it("E-03: Save in edit mode is enabled and submits to the VERSIONS endpoint, not createStrategy", async () => {
        mockGetStrategy.mockResolvedValue(existingAdaptiveDepth);
        mockCreateStrategyVersion.mockResolvedValue({ strategy_id: "adaptive_depth", version: 2 });

        renderForm({ strategyId: "adaptive_depth" });
        await screen.findByDisplayValue("adaptive_depth");

        const saveBtn = screen.getByRole("button", { name: /save as new version/i });
        expect(saveBtn.disabled).toBe(false); // E-03 enables it; E-02 had this disabled

        fireEvent.click(saveBtn);

        await waitFor(() => {
            expect(mockCreateStrategyVersion).toHaveBeenCalledTimes(1);
        });

        // Correct strategy_id used, and routed through the versions endpoint only.
        const [calledStrategyId, calledPayload] = mockCreateStrategyVersion.mock.calls[0];
        expect(calledStrategyId).toBe("adaptive_depth");
        expect(calledPayload.strategy_id).toBe("adaptive_depth");
        expect(calledPayload.name).toBe("Adaptive Depth");

        // A new version must never be submitted through the create-strategy
        // (version-1-only) endpoint.
        expect(mockCreateStrategy).not.toHaveBeenCalled();

        await waitFor(() => {
            expect(mockNavigate).toHaveBeenCalledWith("/admin/strategies/adaptive_depth");
        });
    });

    it("E-03: disables the Save button while a version-create request is in flight (prevents duplicate submits)", async () => {
        mockGetStrategy.mockResolvedValue(existingAdaptiveDepth);
        let resolveCreate;
        mockCreateStrategyVersion.mockReturnValue(
            new Promise((resolve) => {
                resolveCreate = resolve;
            })
        );

        renderForm({ strategyId: "adaptive_depth" });
        await screen.findByDisplayValue("adaptive_depth");

        // Grab a stable reference before submitting: once isLoading is true,
        // Button.jsx swaps its text content for a spinner, so the button can
        // no longer be queried by its "Save as New Version" accessible name.
        const saveBtn = screen.getByRole("button", { name: /save as new version/i });
        fireEvent.click(saveBtn);

        await waitFor(() => {
            expect(mockCreateStrategyVersion).toHaveBeenCalledTimes(1);
        });

        // Button becomes disabled (isLoading) while the request is pending.
        expect(saveBtn.disabled).toBe(true);

        // A second click while pending must not fire a second request.
        fireEvent.click(saveBtn);
        expect(mockCreateStrategyVersion).toHaveBeenCalledTimes(1);

        resolveCreate({ strategy_id: "adaptive_depth", version: 2 });
        await waitFor(() => {
            expect(mockNavigate).toHaveBeenCalled();
        });
    });

    it("E-03: shows the backend error and does not navigate when version creation fails", async () => {
        mockGetStrategy.mockResolvedValue(existingAdaptiveDepth);
        mockCreateStrategyVersion.mockRejectedValue(new Error("strategy_id in body must match path"));

        renderForm({ strategyId: "adaptive_depth" });
        await screen.findByDisplayValue("adaptive_depth");

        fireEvent.click(screen.getByRole("button", { name: /save as new version/i }));

        await waitFor(() => {
            expect(screen.getAllByText(/strategy_id in body must match path/i).length).toBeGreaterThan(0);
        });
        expect(mockNavigate).not.toHaveBeenCalled();
    });

    it("shows a load error and does not render the form if fetching the existing strategy fails", async () => {
        mockGetStrategy.mockRejectedValue(new Error("network error"));
        renderForm({ strategyId: "adaptive_depth" });

        await waitFor(() => {
            expect(screen.getByText(/unable to load this strategy/i)).toBeTruthy();
        });
        expect(screen.queryByRole("button", { name: /create strategy/i })).toBeNull();
    });
});
