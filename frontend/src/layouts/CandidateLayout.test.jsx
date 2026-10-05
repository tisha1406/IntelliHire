/**
 * @vitest-environment jsdom
 *
 * Covers the sidebar_auto_collapse wiring added to CandidateLayout: the
 * saved preference should only affect the sidebar's INITIAL state, and only
 * at the existing small-screen breakpoint (matches sidebar.css's own
 * @media max-width: 992px rule) -- desktop must always start exactly as
 * before (expanded), regardless of this preference.
 */
import React from "react";
import { render, screen, cleanup } from "@testing-library/react";
import { vi, describe, it, expect, afterEach } from "vitest";
import CandidateLayout from "./CandidateLayout";

let mockSettings;

vi.mock("../hooks/candidate/useCandidatePreferences", () => ({
    useApplyCandidatePreferences: () => mockSettings,
}));

vi.mock("../hooks/useSidebar", () => {
    return {
        default: () => {
            const [collapsed, setCollapsed] = React.useState(false);
            return { collapsed, setCollapsed, toggleSidebar: () => setCollapsed(!collapsed) };
        }
    };
});

vi.mock("../components/candidate/CandidateSidebar", () => ({
    default: ({ collapsed }) => <div data-testid="sidebar" data-collapsed={collapsed} />,
}));

vi.mock("../components/candidate/CandidateTopbar", () => ({
    default: () => <div data-testid="topbar" />,
}));

vi.mock("../routes/CandidateRoutes", () => ({
    default: () => <div data-testid="routes" />,
}));

function mockMatchMedia(matches) {
    window.matchMedia = vi.fn().mockImplementation((query) => ({
        matches,
        media: query,
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
    }));
}

describe("CandidateLayout — sidebar_auto_collapse", () => {
    afterEach(() => {
        cleanup();
        vi.restoreAllMocks();
    });

    it("starts collapsed on a small screen when sidebar_auto_collapse is enabled", () => {
        mockMatchMedia(true); // small screen
        mockSettings = { sidebar_auto_collapse: true };

        render(<CandidateLayout />);

        expect(screen.getByTestId("sidebar").dataset.collapsed).toBe("true");
    });

    it("stays expanded on a small screen when sidebar_auto_collapse is disabled", () => {
        mockMatchMedia(true); // small screen
        mockSettings = { sidebar_auto_collapse: false };

        render(<CandidateLayout />);

        expect(screen.getByTestId("sidebar").dataset.collapsed).toBe("false");
    });

    it("preserves existing desktop behavior (always expanded) even when sidebar_auto_collapse is enabled", () => {
        mockMatchMedia(false); // desktop / large screen
        mockSettings = { sidebar_auto_collapse: true };

        render(<CandidateLayout />);

        expect(screen.getByTestId("sidebar").dataset.collapsed).toBe("false");
    });

    it("defaults to expanded while settings have not loaded yet", () => {
        mockMatchMedia(true);
        mockSettings = undefined;

        render(<CandidateLayout />);

        expect(screen.getByTestId("sidebar").dataset.collapsed).toBe("false");
    });
});
