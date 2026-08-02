import { useState } from "react";
import CandidateSidebar from "../components/candidate/CandidateSidebar";
import CandidateTopbar from "../components/candidate/CandidateTopbar";
import CandidateRoutes from "../routes/CandidateRoutes";

import "../styles/candidate/layout.css";
import "../styles/candidate/sidebar.css";
import "../styles/candidate/topbar.css";
import "../styles/candidate/common.css";
import "../styles/candidate/dashboard.css";
import "../styles/candidate/interview.css";
import "../styles/candidate/resume.css";

export default function CandidateLayout() {
    const [collapsed, setCollapsed] = useState(false);

    const toggleSidebar = () => setCollapsed((prev) => !prev);

    return (
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
    );
}