import { NavLink } from "react-router-dom";
import { FaChevronLeft, FaSignOutAlt } from "react-icons/fa";
import {
    FaRobot,
    FaChartPie,
    FaBriefcase,
    FaUsers,
    FaUserCircle,
    FaBell
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
                path: "/recruiter/dashboard",
                icon: <FaChartPie />,
            }
        ]
    },
    {
        title: "Recruitment",
        items: [
            {
                title: "My Campaigns",
                path: "/recruiter/campaigns",
                icon: <FaBriefcase />,
            },
            {
                title: "My Candidates",
                path: "/recruiter/candidates",
                icon: <FaUsers />,
            },
            {
                title: "Interview Sessions",
                path: "/recruiter/interviews",
                icon: <FaRobot />,
            }
        ]
    },
    {
        title: "Account",
        items: [
            {
                title: "Notifications",
                path: "/recruiter/notifications",
                icon: <FaBell />,
            },
            {
                title: "My Profile",
                path: "/recruiter/profile",
                icon: <FaUserCircle />,
            }
        ]
    }
];

function RecruiterSidebar({ sidebarOpen, setSidebarOpen }) {
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
                            <span>Recruiter Portal</span>
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

export default RecruiterSidebar;
