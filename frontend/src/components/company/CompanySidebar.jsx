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
    FaBuilding
} from "react-icons/fa";
import useAuth from "../../hooks/useAuth";

import "../../styles/company/CompanySidebar.css";
import "../../styles/company/overlay.css";

const menuGroups = [
    {
        title: null,
        items: [
            {
                title: "Dashboard",
                path: "/company/dashboard",
                icon: <FaChartPie />,
            }
        ]
    },
    {
        title: "Recruitment",
        items: [
            {
                title: "Campaigns",
                path: "/company/campaigns",
                icon: <FaBriefcase />,
            },
            {
                title: "Job Openings",
                path: "/company/jobs",
                icon: <FaClipboardList />,
            },
            {
                title: "Candidates",
                path: "/company/candidates",
                icon: <FaUsers />,
            },
            {
                title: "AI Interviews",
                path: "/company/interviews",
                icon: <FaRobot />,
            }
        ]
    },
    {
        title: "Analytics",
        items: [
            {
                title: "Hiring Analytics",
                path: "/company/analytics",
                icon: <FaChartBar />,
            },
            {
                title: "Reports",
                path: "/company/reports",
                icon: <FaFileAlt />,
            },
            {
                title: "Exports",
                path: "/company/exports",
                icon: <FaFileExport />,
            }
        ]
    },
    {
        title: "Company",
        items: [
            {
                title: "Team Members",
                path: "/company/team",
                icon: <FaUserFriends />,
            },
            {
                title: "Notifications",
                path: "/company/notifications",
                icon: <FaBell />,
            },
            {
                title: "Company Profile",
                path: "/company/profile",
                icon: <FaBuilding />,
            },
            {
                title: "Settings",
                path: "/company/settings",
                icon: <FaCog />,
            }
        ]
    }
];

function CompanySidebar({ sidebarOpen, setSidebarOpen }) {
    const { logout, companyProfile } = useAuth();
    const companyName = companyProfile?.company_name || localStorage.getItem("companyName") || "Company Portal";

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
                            <span>Company Portal</span>
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
                                {group.items.map((item) => (
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
                                ))}
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