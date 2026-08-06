import { useState } from "react";
import { Bell, Sun, Moon, FileText, Settings, LogOut, User, Menu, CheckCircle2, Clock } from "lucide-react";
import { Link } from "react-router-dom";

import useTheme from "../../hooks/useTheme";
import useSidebar from "../../hooks/useSidebar";
import { useAuthContext } from "../../context/AuthContext";
import { useCandidateDashboard, useCandidateNotifications, useMarkNotificationsRead } from "../../hooks/candidate/useCandidate";

import "../../styles/candidate/topbar.css";

export default function CandidateTopbar() {
    const { theme, toggleTheme } = useTheme();
    const { toggleSidebar } = useSidebar();
    const { logout, user } = useAuthContext();
    const [showNotifications, setShowNotifications] = useState(false);
    const [showProfile, setShowProfile] = useState(false);

    const { data: dashboard, isLoading: dashboardLoading } = useCandidateDashboard();
    const { data: notificationsData } = useCandidateNotifications();
    const { mutate: markRead } = useMarkNotificationsRead();

    const notifications = notificationsData?.notifications || [];
    const unreadCount = notificationsData?.unread_count || 0;

    const markAllRead = () => {
        markRead(null); // null marks all
    };

    return (
        <header className="c-topbar">
            {/* Left side: Context */}
            <div className="c-topbar-context">
                <button className="c-icon-btn d-md-none" onClick={toggleSidebar}>
                    <Menu size={20} />
                </button>
                
                <div className="c-context-item">
                    <span className="c-context-label">Campaign</span>
                    <span className="c-context-value">
                        {dashboardLoading ? "Loading..." : (dashboard?.campaign_name || "—")}
                    </span>
                </div>
                
                <div className="c-topbar-divider" />
                
                <div className="c-context-item">
                    <span className="c-context-label">Role</span>
                    <span className="c-context-value">
                        {dashboardLoading ? "Loading..." : (dashboard?.job_position || "—")}
                    </span>
                </div>

                <div className="c-topbar-divider" />
                
                <div className="c-context-item">
                    <span className="c-context-label">Status</span>
                    <span className="c-context-value">
                        {dashboard?.next_action === "COMPLETED" ? (
                            <><span className="c-status-dot completed"></span> Interview Completed</>
                        ) : (
                            <><span className="c-status-dot pending"></span> Action Required</>
                        )}
                    </span>
                </div>
            </div>

            {/* Right side: Actions */}
            <div className="c-topbar-actions">
                
                {/* Theme Toggle */}
                <button className="c-icon-btn" onClick={toggleTheme} title="Toggle Theme">
                    {theme === "dark" ? <Sun size={18} /> : <Moon size={18} />}
                </button>

                {/* Notifications */}
                <div className="c-dropdown-container">
                    <button
                        className={`c-icon-btn ${showNotifications ? "active" : ""}`}
                        onClick={() => { setShowNotifications(!showNotifications); setShowProfile(false); }}
                    >
                        <Bell size={18} />
                        {unreadCount > 0 && <span className="c-notification-badge" />}
                    </button>

                    {showNotifications && (
                        <div className="c-dropdown-menu c-notifications-menu">
                            <div className="c-dropdown-header">
                                <span className="c-dropdown-title">Notifications</span>
                                {unreadCount > 0 && (
                                    <button className="c-text-btn" onClick={markAllRead}>Mark all read</button>
                                )}
                            </div>
                            <div className="c-notifications-list">
                                {notifications.length > 0 ? (
                                    notifications.map(n => (
                                        <div key={n.id} className={`c-notification-item ${!n.read ? "unread" : ""}`}>
                                            <div className="c-notification-icon">
                                                {n.type === "resume" ? <FileText size={14} /> : <Bell size={14} />}
                                            </div>
                                            <div className="c-notification-content">
                                                <div className="c-notification-title">{n.title}</div>
                                                <div className="c-notification-time">{n.time}</div>
                                            </div>
                                            {!n.read && <div className="c-unread-dot" />}
                                        </div>
                                    ))
                                ) : (
                                    <div className="c-notification-empty">No notifications</div>
                                )}
                            </div>
                        </div>
                    )}
                </div>

                {/* Profile Dropdown */}
                <div className="c-dropdown-container">
                    <button
                        className="c-profile-btn"
                        onClick={() => { setShowProfile(!showProfile); setShowNotifications(false); }}
                    >
                        <div className="c-avatar-small">{dashboard?.candidate_name ? dashboard.candidate_name.charAt(0) : "U"}</div>
                    </button>

                    {showProfile && (
                        <div className="c-dropdown-menu c-profile-menu">
                            <div className="c-profile-header">
                                <div className="c-profile-name">{dashboard?.candidate_name || "Candidate"}</div>
                                <div className="c-profile-email">{dashboard?.candidate_email || user?.email}</div>
                            </div>
                            <div className="c-dropdown-divider" />
                            <Link to="/candidate/profile" className="c-dropdown-item" onClick={() => setShowProfile(false)}>
                                <User size={15} /> My Profile
                            </Link>
                            <Link to="/candidate/settings" className="c-dropdown-item" onClick={() => setShowProfile(false)}>
                                <Settings size={15} /> Settings
                            </Link>
                            <div className="c-dropdown-divider" />
                            <button className="c-dropdown-item c-text-danger" onClick={logout}>
                                <LogOut size={15} /> Log Out
                            </button>
                        </div>
                    )}
                </div>
            </div>
        </header>
    );
}
