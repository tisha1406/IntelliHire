import { NavLink } from "react-router-dom";
import { FaChevronLeft, FaSignOutAlt } from "react-icons/fa";
import {
    FaRobot,
    FaChartPie,
    FaBriefcase,
    FaUsers,
    FaChartBar,
    FaFileExport,
    FaUserCircle,
    FaCog,
    FaClipboardList,
    FaFileAlt,
    FaUserFriends,
    FaBell,
    FaBuilding,
    FaUserTie
} from "react-icons/fa";
import useAuth from "../../hooks/useAuth";
import { usePermissions } from "../../context/PermissionsContext";

import "../../styles/company/CompanySidebar.css";
import "../../styles/company/overlay.css";

// ─── Company Admin Menu ─────────────────────────────────────────────────────
const companyMenuGroups = [
    {
        title: null,
        items: [
            { title: "Dashboard", path: "/company/dashboard", icon: <FaChartPie /> }
        ]
    },
    {
        title: "Recruitment",
        items: [
            { title: "Campaigns",     path: "/company/campaigns",   icon: <FaBriefcase /> },
            { title: "Job Openings",  path: "/company/jobs",        icon: <FaClipboardList /> },
            { title: "Candidates",    path: "/company/candidates",  icon: <FaUsers /> },
            { title: "AI Interviews", path: "/company/interviews",  icon: <FaRobot /> },
        ]
    },
    {
        title: "Analytics",
        items: [
            { title: "Hiring Analytics", path: "/company/analytics", icon: <FaChartBar />,   feature: "analytics" },
            { title: "Reports",          path: "/company/reports",   icon: <FaFileAlt />,    feature: "reports" },
            { title: "Exports",          path: "/company/exports",   icon: <FaFileExport />, feature: "export_reports" },
        ]
    },
    {
        title: "Company",
        items: [
            { title: "Recruiters",       path: "/company/recruiters",     icon: <FaUserTie /> },
            { title: "Team Members",     path: "/company/team",           icon: <FaUserFriends /> },
            { title: "Notifications",    path: "/company/notifications",  icon: <FaBell /> },
            { title: "Company Profile",  path: "/company/profile",        icon: <FaBuilding /> },
            { title: "Settings",         path: "/company/settings",       icon: <FaCog /> },
        ]
    }
];

// ─── Recruiter Menu ─────────────────────────────────────────────────────────
// All paths are under /company/* — recruiters are INSIDE the company workspace.
// The backend automatically scopes data by recruiter_id via JWT.
const recruiterMenuGroups = [
    {
        title: null,
        items: [
            { title: "Dashboard", path: "/company/dashboard", icon: <FaChartPie /> }
        ]
    },
    {
        title: "My Work",
        items: [
            { title: "Campaigns",         path: "/company/campaigns",    icon: <FaBriefcase /> },
            { title: "Candidates",        path: "/company/candidates",   icon: <FaUsers /> },
            { title: "Interview Sessions",path: "/company/interviews",   icon: <FaRobot /> },
        ]
    },
    {
        title: "Account",
        items: [
            { title: "Notifications",  path: "/company/notifications", icon: <FaBell /> },
            { title: "My Profile",     path: "/company/profile",       icon: <FaUserCircle /> },
        ]
    }
];

function CompanySidebar({ sidebarOpen, setSidebarOpen }) {
    const { logout, companyProfile, user, isRecruiter, recruiterProfile } = useAuth();
    const { hasFeature } = usePermissions();

    // Determine display name for sidebar header.
    // companyProfile is now populated for both Company Admins and Recruiters.
    const companyName =
        companyProfile?.company_name ||
        "Company Portal";

    // Choose menu based on role
    const menuGroups = isRecruiter ? recruiterMenuGroups : companyMenuGroups;

    // Role label for sidebar branding
    const roleLabel = isRecruiter ? "Recruiter" : "Company Admin";
    const portalLabel = `Company Portal · ${roleLabel}`;

    return (
        <>
            {/* Overlay */}
            {sidebarOpen && (
                <div
                    className="sidebar-overlay"
                    onClick={() => setSidebarOpen(false)}
                />
            )}

            {/* Sidebar */}
            <aside
                className={
                    sidebarOpen
                        ? "company-sidebar open"
                        : "company-sidebar"
                }
            >
                <div className="sidebar-header">
                    <button
                        className="sidebar-toggle"
                        onClick={() => setSidebarOpen(false)}
                    >
                        <FaChevronLeft />
                    </button>

                    <div className="sidebar-logo">
                        <FaRobot className="logo-icon" />
                        <div>
                            <h2>{companyName}</h2>
                            <span>{portalLabel}</span>
                        </div>
                    </div>
                </div>

                <nav className="sidebar-navigation-scrollable">
                    {menuGroups.map((group, gIdx) => (
                        <div key={gIdx} className="sidebar-menu-group">
                            {group.title && (
                                <h4 className="sidebar-group-header">{group.title}</h4>
                            )}
                            <div className="sidebar-menu-list">
                                {group.items.map((item) => {
                                    // Feature-gate only applies to company admin items
                                    if (item.feature && !hasFeature(item.feature)) {
                                        return null;
                                    }
                                    return (
                                        <NavLink
                                            key={item.title}
                                            to={item.path}
                                            className={({ isActive }) =>
                                                isActive
                                                    ? "sidebar-item active"
                                                    : "sidebar-item"
                                            }
                                            onClick={() => setSidebarOpen(false)}
                                        >
                                            {item.icon}
                                            <span>{item.title}</span>
                                        </NavLink>
                                    );
                                })}
                            </div>
                        </div>
                    ))}
                </nav>

                <button
                    className="logout-btn"
                    onClick={() => {
                        logout();
                        setSidebarOpen(false);
                    }}
                >
                    <FaSignOutAlt />
                    <span>Logout</span>
                </button>
            </aside>
        </>
    );
}

export default CompanySidebar;