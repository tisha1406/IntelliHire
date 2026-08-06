import React, { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
    FaBell, FaBriefcase, FaUser, FaCog, FaShieldAlt,
    FaCheckDouble, FaTrash, FaFilter
} from "react-icons/fa";

import PageHeader from "../../components/common/PageHeader";
import Button from "../../components/common/Button";
import notificationService from "../../services/company/notificationService";

import "../../styles/company/Notifications.css";

const TYPE_META = {
    recruitment: { icon: <FaBriefcase />, label: "Recruitment", color: "#6366F1" },
    candidate:   { icon: <FaUser />,      label: "Candidate",   color: "#10B981" },
    system:      { icon: <FaCog />,       label: "System",      color: "#F59E0B" },
    security:    { icon: <FaShieldAlt />, label: "Security",    color: "#EF4444" },
};

const NOTIF_SETTINGS = [
    { key: "new_applications", label: "New Applications", desc: "Get notified when a new candidate applies", defaultOn: true },
    { key: "ai_screening", label: "AI Screening Updates", desc: "Score updates from AI assessments", defaultOn: true },
    { key: "interviews", label: "Interview Reminders", desc: "Upcoming interview alerts", defaultOn: true },
    { key: "campaign_alerts", label: "Campaign Alerts", desc: "Deadline & status changes", defaultOn: true },
    { key: "security", label: "Security Alerts", desc: "Login activity and API access", defaultOn: true },
    { key: "system", label: "System Updates", desc: "Model upgrades, maintenance, billing", defaultOn: false },
];

const FILTERS = ["All", "recruitment", "candidate", "system", "security"];

export default function Notifications() {
    const [activeFilter, setActiveFilter] = useState("All");
    const [notifications, setNotifications] = useState([]);
    const [loading, setLoading] = useState(true);
    const [settings, setSettings] = useState(
        Object.fromEntries(NOTIF_SETTINGS.map(s => [s.key, s.defaultOn]))
    );

    // Load notifications from backend on mount
    useEffect(() => {
        const load = async () => {
            try {
                const res = await notificationService.getNotifications(100, 0);
                const raw = res.data?.data || res.data || [];
                // Normalize backend shape to match UI shape
                const normalized = raw.map(n => ({
                    id: n.id || n._id,
                    type: n.type || "system",
                    title: n.title || "",
                    message: n.message || "",
                    time: n.created_at
                        ? new Date(n.created_at).toLocaleDateString()
                        : "",
                    unread: !n.is_read,
                    action: n.action || null,
                }));
                setNotifications(normalized);
            } catch (err) {
                console.error("Failed to load notifications:", err);
                setNotifications([]);
            } finally {
                setLoading(false);
            }
        };
        load();
    }, []);

    const filtered = notifications.filter(n =>
        activeFilter === "All" || n.type === activeFilter
    );

    const unreadCount = notifications.filter(n => n.unread).length;
    const typeCounts = FILTERS.slice(1).reduce((acc, t) => {
        acc[t] = notifications.filter(n => n.type === t).length;
        return acc;
    }, {});

    const markAllRead = async () => {
        try {
            await notificationService.markAllRead();
        } catch { /* update locally even if API fails */ }
        setNotifications(prev => prev.map(n => ({ ...n, unread: false })));
    };

    const dismissNotif = (id, e) => {
        e.stopPropagation();
        setNotifications(prev => prev.filter(n => n.id !== id));
    };

    const markRead = async (id) => {
        try {
            await notificationService.markRead(id);
        } catch { /* update locally even if API fails */ }
        setNotifications(prev => prev.map(n => n.id === id ? { ...n, unread: false } : n));
    };

    const toggleSetting = (key) => {
        setSettings(prev => ({ ...prev, [key]: !prev[key] }));
    };

    return (
        <div className="notifications-page">
            <PageHeader
                title="Notifications"
                subtitle={`You have ${unreadCount} unread notification${unreadCount !== 1 ? "s" : ""}.`}
                icon={<FaBell />}
                actions={
                    <Button variant="outline" icon={<FaCheckDouble />} size="sm" onClick={markAllRead}>
                        Mark All as Read
                    </Button>
                }
            />

            {/* Filter Chips */}
            <div className="notif-filter-bar">
                <FaFilter size={11} style={{ color: "var(--text-secondary)" }} />
                {FILTERS.map(f => {
                    const meta = TYPE_META[f];
                    return (
                        <button
                            key={f}
                            className={`notif-filter-chip type-${f} ${activeFilter === f ? "active" : ""}`}
                            onClick={() => setActiveFilter(f)}
                            style={activeFilter === f && meta ? { background: meta.color, borderColor: meta.color } : {}}
                        >
                            {meta && meta.icon}
                            {f === "All" ? "All" : meta?.label}
                            {f !== "All" && (
                                <span style={{
                                    background: "rgba(255,255,255,0.2)",
                                    borderRadius: "999px", padding: "1px 6px", fontSize: "10px"
                                }}>
                                    {typeCounts[f] || 0}
                                </span>
                            )}
                        </button>
                    );
                })}
            </div>

            <div className="notifications-body">
                {/* Notifications List */}
                <div className="notifications-list-panel">
                    <div className="notif-list-header">
                        <h4>
                            {activeFilter === "All" ? "All Notifications" : `${TYPE_META[activeFilter]?.label} Notifications`}
                            <span style={{ marginLeft: 8, fontSize: 12, color: "var(--text-secondary)", fontWeight: 400 }}>
                                ({filtered.length})
                            </span>
                        </h4>
                        <button className="mark-all-btn" onClick={markAllRead}>
                            Mark all read
                        </button>
                    </div>

                    <AnimatePresence initial={false}>
                        {filtered.map((notif, i) => {
                            const meta = TYPE_META[notif.type] || TYPE_META.system;
                            return (
                                <motion.div
                                    key={notif.id}
                                    layout
                                    initial={{ opacity: 0, x: -10 }}
                                    animate={{ opacity: 1, x: 0 }}
                                    exit={{ opacity: 0, x: 20, height: 0, padding: 0 }}
                                    transition={{ duration: 0.25, delay: i * 0.03 }}
                                    className={`notif-item ${notif.unread ? "unread" : "read"}`}
                                    onClick={() => markRead(notif.id)}
                                >
                                    <div className={`notif-type-icon ${notif.type}`}>
                                        {meta.icon}
                                    </div>

                                    <div className="notif-content">
                                        <div className="notif-title-row">
                                            <h5>{notif.title}</h5>
                                            <span className="notif-time">{notif.time}</span>
                                        </div>
                                        <p className="notif-message">{notif.message}</p>
                                    </div>

                                    {notif.unread && <div className="notif-unread-dot" />}

                                    <button
                                        onClick={(e) => dismissNotif(notif.id, e)}
                                        style={{
                                            background: "transparent", border: "none",
                                            color: "var(--text-secondary)", cursor: "pointer",
                                            fontSize: 11, padding: 4, opacity: 0,
                                            transition: "opacity 0.15s"
                                        }}
                                        onMouseEnter={e => e.currentTarget.style.opacity = 1}
                                        onMouseLeave={e => e.currentTarget.style.opacity = 0}
                                        title="Dismiss"
                                    >
                                        <FaTrash />
                                    </button>
                                </motion.div>
                            );
                        })}
                        {filtered.length === 0 && (
                            <motion.div
                                initial={{ opacity: 0 }}
                                animate={{ opacity: 1 }}
                                style={{
                                    textAlign: "center", padding: "60px 20px",
                                    color: "var(--text-secondary)"
                                }}
                            >
                                <FaBell style={{ fontSize: 32, marginBottom: 12, opacity: 0.3 }} />
                                <p>No notifications in this category.</p>
                            </motion.div>
                        )}
                    </AnimatePresence>
                </div>

                {/* Sidebar */}
                <div className="notif-sidebar">
                    {/* Summary */}
                    <motion.div
                        className="notif-summary-card"
                        initial={{ opacity: 0, x: 20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: 0.25 }}
                    >
                        <h4>Notification Summary</h4>
                        {FILTERS.slice(1).map(f => {
                            const meta = TYPE_META[f];
                            return (
                                <div key={f} className="notif-summary-row">
                                    <div className="notif-summary-type">
                                        <div className="notif-summary-dot" style={{ background: meta.color }} />
                                        {meta.label}
                                    </div>
                                    <span className="notif-summary-count">{typeCounts[f] || 0}</span>
                                </div>
                            );
                        })}
                        <div style={{ borderTop: "1px solid var(--border)", paddingTop: 12, marginTop: 8 }}>
                            <div className="notif-summary-row">
                                <span style={{ fontSize: 13, fontWeight: 600, color: "var(--text)" }}>Total Unread</span>
                                <span className="notif-summary-count" style={{ color: "var(--primary)" }}>{unreadCount}</span>
                            </div>
                        </div>
                    </motion.div>

                    {/* Settings */}
                    <motion.div
                        className="notif-settings-card"
                        initial={{ opacity: 0, x: 20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: 0.35 }}
                    >
                        <h4>Notification Preferences</h4>
                        {NOTIF_SETTINGS.map(s => (
                            <div key={s.key} className="notif-setting-row">
                                <div className="notif-setting-info">
                                    <h6>{s.label}</h6>
                                    <p>{s.desc}</p>
                                </div>
                                <label className="toggle-switch">
                                    <input
                                        type="checkbox"
                                        checked={settings[s.key]}
                                        onChange={() => toggleSetting(s.key)}
                                    />
                                    <span className="toggle-slider" />
                                </label>
                            </div>
                        ))}
                    </motion.div>
                </div>
            </div>
        </div>
    );
}
