import { useState, useRef, useEffect } from "react";
import { useNavigate } from "react-router-dom";

import {
    FaBell,
    FaMoon,
    FaSearch,
    FaChevronDown,
    FaUser,
    FaCog,
    FaSignOutAlt,
    FaCheckDouble,
    FaLock,
    FaBars,
    FaRobot,
} from "react-icons/fa";

import { useTheme } from "../../context/ThemeContext";
import { useAuthContext } from "../../context/AuthContext";

import "../../styles/company/CompanyNavbar.css";

function CompanyNavbar({ sidebarOpen, setSidebarOpen }) {

    const navigate = useNavigate();
    const { toggleTheme } = useTheme();
    const { user, logout, companyProfile, recruiterProfile, isRecruiter } = useAuthContext();

    // ── Company branding ───────────────────────────────────────────────────
    // Both Company Admin and Recruiter share the same companyProfile from AuthContext.
    // For recruiters, companyProfile is fetched from /company/profile using company_id.
    const companyName = companyProfile?.company_name || "Company Portal";
    const companyLogo = companyProfile?.logo || null;
    const roleBadgeLabel = isRecruiter ? "Recruiter" : "Company Admin";

    // Derive initials from company name for the logo fallback
    const companyInitials = companyName
        .split(" ")
        .filter(Boolean)
        .map(w => w[0])
        .join("")
        .slice(0, 2)
        .toUpperCase();

    const [showNotifications, setShowNotifications] = useState(false);
    const [showProfile, setShowProfile] = useState(false);

    const [notifications, setNotifications] = useState([
        { id: 1, text: "New candidate applied", time: "2 min ago", read: false },
        { id: 2, text: "AI interview completed", time: "15 min ago", read: false },
        { id: 3, text: "Campaign deadline tomorrow", time: "Today", read: true },
        { id: 4, text: "Report generated", time: "Yesterday", read: true },
    ]);

    const notifRef = useRef(null);
    const profileRef = useRef(null);

    useEffect(() => {

        function closeMenus(e) {
            if (notifRef.current && !notifRef.current.contains(e.target)) {
                setShowNotifications(false);
            }
            if (profileRef.current && !profileRef.current.contains(e.target)) {
                setShowProfile(false);
            }
        }

        document.addEventListener("mousedown", closeMenus);
        return () => document.removeEventListener("mousedown", closeMenus);

    }, []);

    const unreadCount = notifications.filter(n => !n.read).length;

    const markAllRead = () => {
        setNotifications(notifications.map(item => ({ ...item, read: true })));
    };

    const handleLogout = () => {
        logout();
        navigate("/login");
    };

    // ── Identity display ───────────────────────────────────────────────────
    // Recruiter: show recruiter's name from profile or JWT
    // Company Admin: show company name from companyProfile
    let displayName, displayEmail;

    if (isRecruiter) {
        const rp = recruiterProfile;
        displayName = rp
            ? `${rp.first_name || ""} ${rp.last_name || ""}`.trim()
            : user?.name || "Recruiter";
        displayEmail = rp?.email || user?.email || "";
    } else {
        displayName = companyProfile?.company_name || user?.name || "Company";
        displayEmail = companyProfile?.contact_email || user?.email || "";
    }

    const initials = displayName
        .split(" ")
        .filter(Boolean)
        .map(n => n[0])
        .join("")
        .slice(0, 2)
        .toUpperCase();

    // ── Profile dropdown navigation ────────────────────────────────────────
    const handleProfileNav = () => {
        navigate("/company/profile");
        setShowProfile(false);
    };

    const handleSettingsNav = () => {
        if (isRecruiter) {
            navigate("/company/change-password");
        } else {
            navigate("/company/settings");
        }
        setShowProfile(false);
    };

    return (

        <header className="company-navbar">

            <div className="navbar-left">

                {/* Mobile sidebar toggle */}
                <button
                    className="nav-icon-btn navbar-hamburger"
                    onClick={() => setSidebarOpen && setSidebarOpen(!sidebarOpen)}
                    aria-label="Toggle sidebar"
                >
                    <FaBars />
                </button>

                {/* Company Branding */}
                <div className="navbar-brand">
                    <div className="navbar-company-logo">
                        {companyLogo
                            ? <img src={companyLogo} alt={companyName} className="navbar-logo-img" />
                            : <span className="navbar-logo-initials"><FaRobot /></span>
                        }
                    </div>
                    <div className="navbar-brand-text">
                        <span className="navbar-company-name">{companyName}</span>
                        <span className="navbar-portal-label">
                            Company Portal
                            <span className="navbar-role-badge">{roleBadgeLabel}</span>
                        </span>
                    </div>
                </div>

            </div>

            <div className="navbar-right">

                {/* Notifications */}
                <div className="dropdown-wrapper" ref={notifRef}>

                    <button
                        className="nav-icon-btn"
                        onClick={() => setShowNotifications(!showNotifications)}
                    >
                        <FaBell />
                        {unreadCount > 0 && <span className="notif-dot" />}
                    </button>

                    {showNotifications && (

                        <div className="dropdown-menu notifications-dropdown">

                            <div className="dropdown-header">
                                <h4>Notifications</h4>
                                <button className="mark-read-btn" onClick={markAllRead}>
                                    <FaCheckDouble />
                                    Mark all
                                </button>
                            </div>

                            <div className="notification-list">
                                {notifications.map(notification => (
                                    <div
                                        key={notification.id}
                                        className={`notification-item ${notification.read ? "read" : "unread"}`}
                                    >
                                        <span className="notification-dot" />
                                        <div className="notification-content">
                                            <p>{notification.text}</p>
                                            <span>{notification.time}</span>
                                        </div>
                                    </div>
                                ))}
                            </div>

                            <div
                                className="dropdown-footer"
                                onClick={() => {
                                    navigate("/company/notifications");
                                    setShowNotifications(false);
                                }}
                            >
                                View all notifications →
                            </div>

                        </div>

                    )}

                </div>

                {/* Theme */}
                <button className="nav-icon-btn" onClick={toggleTheme}>
                    <FaMoon />
                </button>

                {/* Profile */}
                <div className="dropdown-wrapper" ref={profileRef}>

                    <button
                        className="profile-trigger"
                        onClick={() => setShowProfile(!showProfile)}
                    >
                        <div className="user-avatar-trigger">{initials}</div>
                        <FaChevronDown />
                    </button>

                    {showProfile && (

                        <div className="dropdown-menu profile-dropdown">

                            <div className="profile-header">
                                <div className="profile-avatar">{initials}</div>
                                <div>
                                    <h5>{displayName}</h5>
                                    <span>{displayEmail}</span>
                                    {isRecruiter && (
                                        <span style={{
                                            display: "block",
                                            fontSize: 11,
                                            color: "var(--primary)",
                                            fontWeight: 600,
                                            marginTop: 2
                                        }}>
                                            Recruiter
                                        </span>
                                    )}
                                </div>
                            </div>

                            <div
                                className="dropdown-item"
                                onClick={handleProfileNav}
                            >
                                <FaUser />
                                {isRecruiter ? "My Profile" : "Profile"}
                            </div>

                            <div
                                className="dropdown-item"
                                onClick={handleSettingsNav}
                            >
                                {isRecruiter ? <FaLock /> : <FaCog />}
                                {isRecruiter ? "Change Password" : "Settings"}
                            </div>

                            <div className="dropdown-divider" />

                            <div
                                className="dropdown-item danger"
                                onClick={handleLogout}
                            >
                                <FaSignOutAlt />
                                Logout
                            </div>

                        </div>

                    )}

                </div>

            </div>

        </header>

    );

}

export default CompanyNavbar;