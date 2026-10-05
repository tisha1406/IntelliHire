/**
 * @vitest-environment jsdom
 */
import React from "react";
import { render, screen, fireEvent, waitFor, within, cleanup } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { vi, describe, it, expect, beforeEach, afterEach } from "vitest";

const mockNavigate = vi.fn();
vi.mock("react-router-dom", async () => {
    const actual = await vi.importActual("react-router-dom");
    return { ...actual, useNavigate: () => mockNavigate };
});

vi.mock("../../context/AuthContext", () => ({
    useAuthContext: () => ({ user: { companyId: "company_1" }, loading: false }),
}));

const mockUsePermissions = vi.fn();
vi.mock("../../context/PermissionsContext", () => ({
    usePermissions: (...args) => mockUsePermissions(...args),
}));

const mockGetStrategies = vi.fn();
vi.mock("../../api/settings", () => ({
    SettingsAPI: { getStrategies: (...args) => mockGetStrategies(...args) },
}));

const mockCreateCampaign = vi.fn();
vi.mock("../../services/company/campaignService", () => ({
    default: { createCampaign: (...args) => mockCreateCampaign(...args) },
}));

vi.mock("../../services/company/recruiterManagementService", () => ({
    default: {},
}));

import NewCampaign from "./NewCampaign.jsx";

const ACTIVE_STRATEGY = {
    strategy_id: "adaptive_depth",
    name: "Adaptive Depth",
    description: "Depth follows demonstrated performance.",
    is_active: true,
    applicable_interview_types: ["technical"],
    budget_mode: "fixed",
    min_questions: 8,
    target_questions: 10,
    max_questions: 12,
    company_override_bounds: { target_questions_min_delta: 0, target_questions_max_delta: 0 },
    difficulty_policy: { band_constrainable: true },
};

// Real production entitlement format (confirmed Task 14 audit): company.allowed_strategies
// stores strategy DISPLAY NAMES (e.g. "Fixed Coverage"), not strategy_id slugs.
const FIXED_COVERAGE_STRATEGY = {
    strategy_id: "fixed_coverage",
    name: "Fixed Coverage",
    description: "Covers a fixed set of topics evenly.",
    is_active: true,
    applicable_interview_types: ["technical", "resume_experience", "hr_behavioral", "situational_case", "mixed"],
    budget_mode: "fixed",
    min_questions: 10,
    target_questions: 10,
    max_questions: 10,
};

const BEHAVIORAL_STRATEGY = {
    strategy_id: "behavioral_adaptive",
    name: "Behavioral Adaptive",
    description: "Adapts behavioral follow-ups.",
    is_active: true,
    applicable_interview_types: ["hr_behavioral"],
    budget_mode: "fixed",
    min_questions: 5,
    target_questions: 8,
    max_questions: 10,
};

function renderPage() {
    return render(
        <MemoryRouter>
            <NewCampaign />
        </MemoryRouter>
    );
}

// Drives the wizard from step 0 through to step 3 (Interview Settings), where
// the Difficulty select lives. Steps 0/1 need minimal valid input; step 2
// ("Requirements") already ships with 2 default requirements, so it's valid
// without any interaction.
async function advanceToInterviewSettingsStep() {
    fireEvent.change(screen.getByPlaceholderText(/lead frontend architect/i), { target: { value: "Senior Engineer" } });
    fireEvent.change(screen.getByLabelText(/^department$/i), { target: { value: "Engineering" } });
    fireEvent.change(screen.getByPlaceholderText(/remote \/ new york/i), { target: { value: "Remote" } });
    const deadlineInput = document.querySelector('input[type="date"]');
    fireEvent.change(deadlineInput, { target: { value: "2026-12-31" } });
    fireEvent.click(screen.getByRole("button", { name: /next/i }));

    await screen.findByText(/job overview/i);
    fireEvent.change(screen.getByLabelText(/^employment type$/i), { target: { value: "Full-time" } });
    fireEvent.change(screen.getByPlaceholderText(/introduce the candidate/i), { target: { value: "A great role." } });
    fireEvent.click(screen.getByRole("button", { name: /next/i }));

    await screen.findByText(/competencies & requirements/i);
    fireEvent.click(screen.getByRole("button", { name: /next/i })); // step 2 is valid by default

    await screen.findByLabelText(/interview strategy/i).catch(() => {}); // settle, actual assertion happens in each test
}

describe("NewCampaign — difficulty option (B-03 regression)", () => {
    beforeEach(() => {
        mockNavigate.mockReset();
        mockGetStrategies.mockReset();
        mockCreateCampaign.mockReset();
        mockUsePermissions.mockReset();
        mockUsePermissions.mockReturnValue({ platform: { allowed_strategies: ["Adaptive Depth"] } });
        mockGetStrategies.mockResolvedValue([ACTIVE_STRATEGY]);
    });

    afterEach(() => {
        cleanup();
    });

    it('does not offer "Adaptive" as a selectable campaign difficulty, and the valid easy/medium/hard options remain', async () => {
        renderPage();
        await advanceToInterviewSettingsStep();

        fireEvent.change(await screen.findByLabelText(/interview strategy/i), { target: { value: "adaptive_depth" } });

        const difficultySelect = await screen.findByLabelText(/^difficulty$/i);
        const optionLabels = within(difficultySelect)
            .getAllByRole("option")
            .map((o) => o.textContent);

        expect(optionLabels).not.toContain("Adaptive");
        expect(optionLabels).toEqual(expect.arrayContaining(["Easy", "Medium", "Hard"]));
    });

    it("submits a valid difficulty value (medium) to the real createCampaign call, never 'adaptive'", async () => {
        renderPage();
        await advanceToInterviewSettingsStep();

        fireEvent.change(await screen.findByLabelText(/interview strategy/i), { target: { value: "adaptive_depth" } });
        const difficultySelect = await screen.findByLabelText(/^difficulty$/i);
        fireEvent.change(difficultySelect, { target: { value: "medium" } });

        fireEvent.click(screen.getByRole("button", { name: /next/i }));
        fireEvent.click(await screen.findByRole("button", { name: /publish|create|submit/i }));

        await waitFor(() => {
            expect(mockCreateCampaign).toHaveBeenCalledTimes(1);
        });
        const payload = mockCreateCampaign.mock.calls[0][0];
        expect(payload.difficulty_band).toBe("medium");
        expect(payload.difficulty_band).not.toBe("adaptive");
    });
});

describe("NewCampaign — strategy entitlement filtering (Task 14 regression)", () => {
    beforeEach(() => {
        mockNavigate.mockReset();
        mockGetStrategies.mockReset();
        mockCreateCampaign.mockReset();
        mockUsePermissions.mockReset();
        mockGetStrategies.mockResolvedValue([ACTIVE_STRATEGY, FIXED_COVERAGE_STRATEGY, BEHAVIORAL_STRATEGY]);
    });

    afterEach(() => {
        cleanup();
    });

    it("shows strategies whose display name is present in allowed_strategies (real production format)", async () => {
        mockUsePermissions.mockReturnValue({
            platform: { allowed_strategies: ["Adaptive Depth", "Fixed Coverage"] },
        });
        renderPage();
        await advanceToInterviewSettingsStep();

        const strategySelect = await screen.findByLabelText(/interview strategy/i);
        const optionLabels = within(strategySelect).getAllByRole("option").map((o) => o.textContent);

        expect(optionLabels).toEqual(expect.arrayContaining(["Adaptive Depth", "Fixed Coverage"]));
    });

    it("excludes a strategy whose display name is not present in allowed_strategies", async () => {
        mockUsePermissions.mockReturnValue({
            platform: { allowed_strategies: ["Adaptive Depth", "Fixed Coverage"] },
        });
        renderPage();
        await advanceToInterviewSettingsStep();

        const strategySelect = await screen.findByLabelText(/interview strategy/i);
        const optionLabels = within(strategySelect).getAllByRole("option").map((o) => o.textContent);

        expect(optionLabels).not.toContain("Behavioral Adaptive");
    });

    it("still applies interview-type filtering on top of the entitlement filter: technical shows only technical-applicable strategies", async () => {
        mockUsePermissions.mockReturnValue({
            platform: { allowed_strategies: ["Adaptive Depth", "Fixed Coverage", "Behavioral Adaptive"] },
        });
        renderPage();
        await advanceToInterviewSettingsStep();

        // formData.interviewType defaults to "technical"; Behavioral Adaptive is only
        // applicable to hr_behavioral, so even though it's entitled, it must not appear.
        const strategySelect = await screen.findByLabelText(/interview strategy/i);
        const optionLabels = within(strategySelect).getAllByRole("option").map((o) => o.textContent);

        expect(optionLabels).toEqual(expect.arrayContaining(["Adaptive Depth", "Fixed Coverage"]));
        expect(optionLabels).not.toContain("Behavioral Adaptive");
    });

    it("retains strategy_id as the option value for submission even though filtering/display use name", async () => {
        mockUsePermissions.mockReturnValue({
            platform: { allowed_strategies: ["Adaptive Depth", "Fixed Coverage"] },
        });
        renderPage();
        await advanceToInterviewSettingsStep();

        const strategySelect = await screen.findByLabelText(/interview strategy/i);
        fireEvent.change(strategySelect, { target: { value: "fixed_coverage" } });

        fireEvent.click(screen.getByRole("button", { name: /next/i }));
        fireEvent.click(await screen.findByRole("button", { name: /publish|create|submit/i }));

        await waitFor(() => {
            expect(mockCreateCampaign).toHaveBeenCalledTimes(1);
        });
        const payload = mockCreateCampaign.mock.calls[0][0];
        expect(payload.strategy_id).toBe("fixed_coverage");
    });
});
