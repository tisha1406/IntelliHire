import { useEffect, useRef } from "react";
import { MotionConfig } from "framer-motion";
import useSidebar from "../hooks/useSidebar";
import CandidateSidebar from "../components/candidate/CandidateSidebar";
import CandidateTopbar from "../components/candidate/CandidateTopbar";
import CandidateRoutes from "../routes/CandidateRoutes";
import { useApplyCandidatePreferences } from "../hooks/candidate/useCandidatePreferences";

import "../styles/candidate/layout.css";
import "../styles/candidate/sidebar.css";
import "../styles/candidate/topbar.css";
import "../styles/candidate/common.css";
import "../styles/candidate/dashboard.css";
import "../styles/candidate/interview.css";
import "../styles/candidate/resume.css";

const SMALL_SCREEN_QUERY = "(max-width: 992px)";

export default function CandidateLayout() {
    const settings = useApplyCandidatePreferences();
    const { collapsed, setCollapsed, toggleSidebar } = useSidebar();
    const appliedAutoCollapse = useRef(false);

    // sidebar_auto_collapse: only affects the initial state at the existing
    // small-screen breakpoint (matches sidebar.css's own @media max-width:
    // 992px rule) -- desktop always starts exactly as before (expanded),
    // regardless of this preference. Applied once, when settings first load,
    // so it never overrides a manual toggle made afterwards.
    useEffect(() => {
        if (!settings || appliedAutoCollapse.current) return;
        appliedAutoCollapse.current = true;

        const isSmallScreen = window.matchMedia(SMALL_SCREEN_QUERY).matches;
        if (isSmallScreen && settings.sidebar_auto_collapse) {
            setCollapsed(true);
        }
    }, [settings, setCollapsed]);
    return (
        <MotionConfig reducedMotion={settings?.reduced_motion ? "always" : "never"}>
            <div className="c-layout">
                {/* Mobile overlay */}
                {!collapsed && (
                    <div
                        className="c-mobile-overlay"
                        onClick={toggleSidebar}
                    />
                )}

                <CandidateSidebar collapsed={collapsed} onToggle={toggleSidebar} />

                <section className="c-main">
                    <CandidateTopbar onMenuToggle={toggleSidebar} />

                    <main className="c-content">
                        <CandidateRoutes />
                    </main>
                </section>
            </div>
        </MotionConfig>
    );
}