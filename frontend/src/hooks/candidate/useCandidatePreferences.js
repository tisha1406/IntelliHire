import { useEffect } from "react";
import { useCandidateSettings } from "./useCandidate";

/**
 * Applies the candidate's saved portal-level preferences (high_contrast,
 * reduced_motion) to the document root, the same mechanism ThemeContext
 * already uses for [data-theme] (see src/context/ThemeContext.jsx).
 *
 * Reuses the existing useCandidateSettings() React Query hook -- same
 * queryKey ("candidate_settings") as Settings.jsx, so mounting this once at
 * the CandidateLayout level does not cause a duplicate GET /settings call;
 * React Query serves both consumers from the same cached request.
 *
 * sidebar_auto_collapse is returned (not applied here) because applying it
 * requires CandidateLayout's own collapsed state, not a DOM attribute.
 */
export function useApplyCandidatePreferences() {
    const { data: settings } = useCandidateSettings();

    useEffect(() => {
        if (!settings) return;

        document.documentElement.setAttribute(
            "data-high-contrast",
            settings.high_contrast ? "true" : "false"
        );
        document.documentElement.setAttribute(
            "data-reduced-motion",
            settings.reduced_motion ? "true" : "false"
        );
    }, [settings?.high_contrast, settings?.reduced_motion]);

    return settings;
}
