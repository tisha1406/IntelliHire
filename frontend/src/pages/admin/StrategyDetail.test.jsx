/**
 * @vitest-environment jsdom
 */
import React from "react";
import { render, screen, fireEvent, waitFor, cleanup } from "@testing-library/react";
import { MemoryRouter, Routes, Route } from "react-router-dom";
import { vi, describe, it, expect, beforeEach, afterEach } from "vitest";

const mockNavigate = vi.fn();
vi.mock("react-router-dom", async () => {
    const actual = await vi.importActual("react-router-dom");
    return { ...actual, useNavigate: () => mockNavigate };
});

const mockGetStrategy = vi.fn();
const mockGetStrategyVersions = vi.fn();
const mockActivateVersion = vi.fn();
vi.mock("../../api/strategies", () => ({
    StrategiesAPI: {
        getStrategy: (...args) => mockGetStrategy(...args),
        getStrategyVersions: (...args) => mockGetStrategyVersions(...args),
        activateVersion: (...args) => mockActivateVersion(...args),
    },
}));

import StrategyDetail from "./StrategyDetail.jsx";

function renderDetail(strategyId = "adaptive_depth") {
    return render(
        <MemoryRouter initialEntries={[`/admin/strategies/${strategyId}`]}>
            <Routes>
                <Route path="/admin/strategies/:strategyId" element={<StrategyDetail />} />
            </Routes>
        </MemoryRouter>
    );
}

const latest = {
    strategy_id: "adaptive_depth",
    name: "Adaptive Depth",
    description: "Depth follows demonstrated performance.",
    version: 2,
    is_active: true,
    applicable_interview_types: ["technical"],
    min_questions: 8,
    target_questions: 10,
    max_questions: 12,
};

const versionList = [
    { ...latest, version: 2, is_active: true },
    { ...latest, version: 1, is_active: false, min_questions: 6, target_questions: 8, max_questions: 10 },
];

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

describe("StrategyDetail (E-03 version history + activation)", () => {
    beforeEach(() => {
        mockNavigate.mockReset();
        mockGetStrategy.mockReset();
        mockGetStrategyVersions.mockReset();
        mockActivateVersion.mockReset();
    });

    afterEach(() => {
        cleanup();
    });

    it("loads version history from the real StrategiesAPI client (no mock data)", async () => {
        mockGetStrategy.mockResolvedValue(latest);
        mockGetStrategyVersions.mockResolvedValue(versionList);

        renderDetail();

        await waitFor(() => {
            expect(mockGetStrategy).toHaveBeenCalledWith("adaptive_depth");
            expect(mockGetStrategyVersions).toHaveBeenCalledWith("adaptive_depth");
        });

        await waitFor(() => {
            expect(screen.getAllByText("v2")[0]).toBeTruthy();
            expect(screen.getAllByText("v1")[0]).toBeTruthy();
        });
    });

    it("renders an Activate button for an inactive version and a Deactivate button for the active one", async () => {
        mockGetStrategy.mockResolvedValue(latest);
        mockGetStrategyVersions.mockResolvedValue(versionList);

        renderDetail();

        await waitFor(() => {
            expect(screen.getAllByText("v2")[0]).toBeTruthy();
        });

        expect(screen.getByRole("button", { name: /^deactivate$/i })).toBeTruthy(); // v2, is_active true
        expect(screen.getByRole("button", { name: /^activate$/i })).toBeTruthy(); // v1, is_active false
    });

    it("clicking Activate calls PATCH .../versions/{version}/activate with the correct strategy_id, version, and is_active, then refreshes", async () => {
        mockGetStrategy.mockResolvedValue(latest);
        mockGetStrategyVersions.mockResolvedValue(versionList);
        mockActivateVersion.mockResolvedValue({ updated_fields: ["is_active"], new_version: 1 });

        renderDetail();
        await waitFor(() => expect(screen.getAllByText("v1")[0]).toBeTruthy());

        const activateBtn = screen.getByRole("button", { name: /^activate$/i });
        fireEvent.click(activateBtn);

        await waitFor(() => {
            expect(mockActivateVersion).toHaveBeenCalledWith("adaptive_depth", 1, true);
        });

        // Refresh: getStrategy/getStrategyVersions called again after the activation resolves.
        await waitFor(() => {
            expect(mockGetStrategy.mock.calls.length).toBeGreaterThanOrEqual(2);
            expect(mockGetStrategyVersions.mock.calls.length).toBeGreaterThanOrEqual(2);
        });
    });

    it("clicking Deactivate sends is_active: false for that version", async () => {
        mockGetStrategy.mockResolvedValue(latest);
        mockGetStrategyVersions.mockResolvedValue(versionList);
        mockActivateVersion.mockResolvedValue({ updated_fields: ["is_active"], new_version: 2 });

        renderDetail();
        await waitFor(() => expect(screen.getAllByText("v2")[0]).toBeTruthy());

        fireEvent.click(screen.getByRole("button", { name: /^deactivate$/i }));

        await waitFor(() => {
            expect(mockActivateVersion).toHaveBeenCalledWith("adaptive_depth", 2, false);
        });
    });

    it("disables the acted-on row's button while the activation request is pending and ignores a second click", async () => {
        mockGetStrategy.mockResolvedValue(latest);
        mockGetStrategyVersions.mockResolvedValue(versionList);
        let resolveActivate;
        mockActivateVersion.mockReturnValue(
            new Promise((resolve) => {
                resolveActivate = resolve;
            })
        );

        renderDetail();
        await waitFor(() => expect(screen.getAllByText("v1")[0]).toBeTruthy());

        const activateBtn = screen.getByRole("button", { name: /^activate$/i });
        fireEvent.click(activateBtn);

        await waitFor(() => {
            expect(mockActivateVersion).toHaveBeenCalledTimes(1);
        });
        expect(activateBtn.disabled).toBe(true);

        fireEvent.click(activateBtn);
        expect(mockActivateVersion).toHaveBeenCalledTimes(1); // still 1 — duplicate click ignored

        resolveActivate({ updated_fields: ["is_active"], new_version: 1 });
        await waitFor(() => {
            expect(activateBtn.disabled).toBe(false);
        });
    });

    it("shows an error state and does not crash when activation fails", async () => {
        mockGetStrategy.mockResolvedValue(latest);
        mockGetStrategyVersions.mockResolvedValue(versionList);
        mockActivateVersion.mockRejectedValue(new Error("Strategy version not found."));

        renderDetail();
        await waitFor(() => expect(screen.getAllByText("v1")[0]).toBeTruthy());

        fireEvent.click(screen.getByRole("button", { name: /^activate$/i }));

        await waitFor(() => {
            expect(screen.getAllByText(/strategy version not found/i).length).toBeGreaterThan(0);
        });
    });

    it("the Edit button still navigates to the edit route (E-01/E-02 behavior unchanged)", async () => {
        mockGetStrategy.mockResolvedValue(latest);
        mockGetStrategyVersions.mockResolvedValue(versionList);

        renderDetail();
        await waitFor(() => expect(screen.getAllByText("v2")[0]).toBeTruthy());

        fireEvent.click(screen.getByRole("button", { name: /^edit$/i }));
        expect(mockNavigate).toHaveBeenCalledWith("/admin/strategies/edit/adaptive_depth");
    });
});
