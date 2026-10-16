/**
 * @vitest-environment jsdom
 */
import React from "react";
import { render, screen, waitFor, cleanup } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { vi, describe, it, expect, afterEach } from "vitest";

const mockGetDashboardStats = vi.fn();
vi.mock("../../api/analytics", () => ({
    AnalyticsAPI: {
        getDashboardStats: (...args) => mockGetDashboardStats(...args),
    },
}));

import Analytics from "./Analytics.jsx";

function renderAnalytics() {
    const client = new QueryClient({
        defaultOptions: { queries: { retry: false } },
    });
    return render(
        <QueryClientProvider client={client}>
            <Analytics />
        </QueryClientProvider>
    );
}

afterEach(() => {
    cleanup();
    vi.clearAllMocks();
});

describe("Analytics (admin)", () => {
    it("renders real KPI values from AnalyticsAPI, not hardcoded mock numbers", async () => {
        mockGetDashboardStats.mockResolvedValue({
            kpis: {
                total_interviews: 42,
                success_rate: 77.5,
                active_companies: 3,
                total_candidates: 9,
            },
            charts: {
                interviews_over_time: [{ name: "Mon", completed: 2, active: 1 }],
                company_growth: [{ name: "Jan", total: 1 }],
            },
            recent_companies: [],
        });

        renderAnalytics();

        // getByText throws (failing the test) if the node is absent, so a
        // successful return already proves the real KPI value rendered.
        await waitFor(() => screen.getByText("42"), { timeout: 5000 });
        expect(screen.getByText("77.5%")).toBeTruthy();
        expect(screen.getByText("3")).toBeTruthy();
        expect(screen.getByText("9")).toBeTruthy();

        // The old hardcoded mock values must never appear.
        expect(screen.queryByText("12,450")).toBeNull();
        expect(screen.queryByText("94.2%")).toBeNull();
        expect(screen.queryByText("342")).toBeNull();
    });

    it("shows a zero-state placeholder, not fabricated data, when charts are empty", async () => {
        mockGetDashboardStats.mockResolvedValue({
            kpis: { total_interviews: 0, success_rate: 0, active_companies: 0, total_candidates: 0 },
            charts: { interviews_over_time: [], company_growth: [] },
            recent_companies: [],
        });

        renderAnalytics();

        await waitFor(() => screen.getByText("No interview activity yet."), { timeout: 5000 });
        expect(screen.getByText("No company data yet.")).toBeTruthy();
    });

    it("surfaces a visible error message when the analytics request fails", async () => {
        mockGetDashboardStats.mockRejectedValue(new Error("network down"));

        renderAnalytics();

        await waitFor(() => screen.getByText(/Could not load analytics/), { timeout: 5000 });
        expect(screen.getByText(/network down/)).toBeTruthy();
    });
});
