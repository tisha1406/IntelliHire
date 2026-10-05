/**
 * @vitest-environment jsdom
 */
import { renderHook } from "@testing-library/react";
import { vi, describe, it, expect, afterEach } from "vitest";
import { useApplyCandidatePreferences } from "./useCandidatePreferences";

let mockSettingsData;

vi.mock("./useCandidate", () => ({
    useCandidateSettings: () => ({ data: mockSettingsData }),
}));

describe("useApplyCandidatePreferences", () => {
    afterEach(() => {
        document.documentElement.removeAttribute("data-high-contrast");
        document.documentElement.removeAttribute("data-reduced-motion");
    });

    it("applies data-high-contrast=true when the saved setting is enabled", () => {
        mockSettingsData = { high_contrast: true, reduced_motion: false };
        renderHook(() => useApplyCandidatePreferences());
        expect(document.documentElement.getAttribute("data-high-contrast")).toBe("true");
    });

    it("applies data-high-contrast=false when the saved setting is disabled", () => {
        mockSettingsData = { high_contrast: false, reduced_motion: false };
        renderHook(() => useApplyCandidatePreferences());
        expect(document.documentElement.getAttribute("data-high-contrast")).toBe("false");
    });

    it("applies data-reduced-motion=true when the saved setting is enabled", () => {
        mockSettingsData = { high_contrast: false, reduced_motion: true };
        renderHook(() => useApplyCandidatePreferences());
        expect(document.documentElement.getAttribute("data-reduced-motion")).toBe("true");
    });

    it("applies data-reduced-motion=false when the saved setting is disabled", () => {
        mockSettingsData = { high_contrast: false, reduced_motion: false };
        renderHook(() => useApplyCandidatePreferences());
        expect(document.documentElement.getAttribute("data-reduced-motion")).toBe("false");
    });

    it("does not set either attribute before settings have loaded", () => {
        mockSettingsData = undefined;
        renderHook(() => useApplyCandidatePreferences());
        expect(document.documentElement.hasAttribute("data-high-contrast")).toBe(false);
        expect(document.documentElement.hasAttribute("data-reduced-motion")).toBe(false);
    });

    it("returns the settings object for callers (e.g. sidebar_auto_collapse)", () => {
        mockSettingsData = { high_contrast: false, reduced_motion: false, sidebar_auto_collapse: true };
        const { result } = renderHook(() => useApplyCandidatePreferences());
        expect(result.current.sidebar_auto_collapse).toBe(true);
    });
});
