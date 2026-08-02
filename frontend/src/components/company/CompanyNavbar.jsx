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
} from "react-icons/fa";

import { useTheme } from "../../context/ThemeContext";
import { useAuthContext } from "../../context/AuthContext";

import "../../styles/company/CompanyNavbar.css";

function CompanyNavbar() {

    const navigate = useNavigate();
    const { toggleTheme } = useTheme();
    const { user, logout } = useAuthContext();

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

    // Derive display values from the real authenticated user
    const displayName = user?.name || "User";
    const displayEmail = user?.email || "";
    const initials = displayName
        .split(" ")
        .map(n => n[0])
        .join("")
        .slice(0, 2)
        .toUpperCase();

    return (

        <header className="company-navbar">

            <div className="navbar-left">
                <div className="nav-search-wrapper">
                    <FaSearch className="nav-search-icon" />
                    <input
                        type="text"
                        placeholder="Search candidates, jobs..."
                        onKeyDown={(e) => {
                            if (e.key === "Enter" && e.target.value.trim()) {
                                navigate(`/company/candidates?search=${encodeURIComponent(e.target.value.trim())}`);
                            }
                        }}
                    />
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
                                </div>
                            </div>

                            <div
                                className="dropdown-item"
                                onClick={() => { navigate("/company/profile"); setShowProfile(false); }}
                            >
                                <FaUser />
                                Profile
                            </div>

                            <div
                                className="dropdown-item"
                                onClick={() => { navigate("/company/settings"); setShowProfile(false); }}
                            >
                                <FaCog />
                                Settings
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