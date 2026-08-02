import { Link, useLocation } from "react-router-dom";
import { LayoutDashboard, FileText, Video, BarChart2, User, Settings, HelpCircle, LogOut, ChevronLeft, ChevronRight, CheckCircle2, Clock } from "lucide-react";
import useSidebar from "../../hooks/useSidebar";
import { useAuthContext } from "../../context/AuthContext";
import { useCandidateDashboard } from "../../hooks/candidate/useCandidate";

import "../../styles/candidate/sidebar.css";

const MENU_ITEMS = [
    { label: "Dashboard", icon: LayoutDashboard, route: "/candidate/dashboard" },
    { label: "Resume", icon: FileText, route: "/candidate/resume" },
    { label: "Interview", icon: Video, route: "/candidate/interview/official" },
    { label: "Reports", icon: BarChart2, route: "/candidate/reports" },
];

const PREFERENCES = [
    { label: "Profile", icon: User, route: "/candidate/profile" },
    { label: "Settings", icon: Settings, route: "/candidate/settings" },
    { label: "Support", icon: HelpCircle, route: "/candidate/support" },
];

export default function CandidateSidebar() {
    const { collapsed, toggleSidebar } = useSidebar();
    const location = useLocation();
    const { logout, user } = useAuthContext();
    const { data: dashboard, isLoading } = useCandidateDashboard();

    const isActive = (path) => location.pathname.startsWith(path);

    return (
        <aside className={`c-sidebar ${collapsed ? "collapsed" : ""}`}>
            {/* Header / Brand */}
            <div className="c-sidebar-header">
                <div className="c-brand">
                    <div className="c-brand-logo">I</div>
                    <div className="c-brand-text">
                        <h2>IntelliHire</h2>
                    </div>
                </div>
                <button className="c-collapse-btn" onClick={toggleSidebar}>
                    {collapsed ? <ChevronRight size={18} /> : <ChevronLeft size={18} />}
                </button>
            </div>

            <div className="c-sidebar-divider" />

            {/* Campaign Widget */}
            <div className="c-sidebar-company">
                <div className="c-company-card" style={{ flexDirection: "column", alignItems: "flex-start", gap: 16 }}>
                    <div style={{ display: "flex", alignItems: "center", gap: 12, width: "100%" }}>
                        <div className="c-company-logo" style={{ flexShrink: 0 }}>
                            {isLoading ? "..." : (dashboard?.company_name ? dashboard.company_name.substring(0, 2).toUpperCase() : "IH")}
                        </div>
                        <div className="c-company-info" style={{ flex: 1, minWidth: 0 }}>
                            <h3 style={{ fontSize: 13, marginBottom: 2, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
                                {isLoading ? "Loading..." : dashboard?.company_name}
                            </h3>
                            <p style={{ fontSize: 11, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
                                {isLoading ? "Loading..." : dashboard?.job_position}
                            </p>
                        </div>
                    </div>
                    {!collapsed && (
                        <div style={{ width: "100%", padding: "12px", background: "rgba(0,0,0,0.2)", borderRadius: 8, border: "1px solid rgba(255,255,255,0.05)" }}>
                            <div style={{ fontSize: 10, color: "var(--text-muted)", textTransform: "uppercase", fontWeight: 600, letterSpacing: 0.5, marginBottom: 4 }}>Campaign</div>
                            <div style={{ fontSize: 12, fontWeight: 500, color: "var(--text)", marginBottom: 12, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
                                {isLoading ? "Loading..." : dashboard?.campaign_name}
                            </div>
                            
                            <div style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 11, color: dashboard?.next_action === "COMPLETED" ? "#10B981" : "#F59E0B", fontWeight: 600 }}>
                                {dashboard?.next_action === "COMPLETED" ? <CheckCircle2 size={12} /> : <Clock size={12} />}
                                {dashboard?.next_action === "COMPLETED" ? "Interview Completed" : "Interview Pending"}
                            </div>
                        </div>
                    )}
                </div>
            </div>

            <div className="c-sidebar-divider" />

            {/* Scrollable Nav Area */}
            <div className="c-sidebar-scroll">
                <nav className="c-nav-group">
                    <div className="c-nav-title">Campaign Navigation</div>
                    {MENU_ITEMS.map((item) => (
                        <Link
                            key={item.route}
                            to={item.route}
                            className={`c-nav-link ${isActive(item.route) ? "active" : ""}`}
                            title={collapsed ? item.label : ""}
                        >
                            <item.icon size={20} className="c-nav-icon" />
                            <span className="c-nav-label">{item.label}</span>
                        </Link>
                    ))}
                </nav>
                
                {!collapsed && <div className="c-sidebar-divider" style={{ width: "100%", opacity: 0.5 }} />}

                <nav className="c-nav-group">
                    <div className="c-nav-title">Candidate Account</div>
                    {PREFERENCES.map((item) => (
                        <Link
                            key={item.route}
                            to={item.route}
                            className={`c-nav-link ${isActive(item.route) ? "active" : ""}`}
                            title={collapsed ? item.label : ""}
                        >
                            <item.icon size={20} className="c-nav-icon" />
                            <span className="c-nav-label">{item.label}</span>
                        </Link>
                    ))}
                </nav>
            </div>

            <div className="c-sidebar-divider" />

            {/* Footer / User Profile */}
            <div className="c-sidebar-footer">
                <div className="c-user-widget">
                    <div className="c-user-avatar">
                        {dashboard?.candidate_name ? dashboard.candidate_name.charAt(0) : "U"}
                    </div>
                    <div className="c-user-info">
                        <span className="c-user-name">{dashboard?.candidate_name || "Candidate"}</span>
                        <span className="c-user-role">Candidate</span>
                    </div>
                    <button className="c-user-logout" onClick={logout} title="Log Out">
                        <LogOut size={18} />
                    </button>
                </div>
            </div>
        </aside>
    );
}
