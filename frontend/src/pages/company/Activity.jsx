import React, { useState } from "react";
import { motion } from "framer-motion";
import {
    FaHistory, FaBriefcase, FaUser, FaCog, FaShieldAlt,
    FaSearch, FaFilter
} from "react-icons/fa";

import PageHeader from "../../components/common/PageHeader";

const ACTIVITY_LOG = [
    { id: 1, type: "recruitment", user: "Sarah Jenkins", action: "Launched campaign", target: "DevOps & Infrastructure Lead", time: "2 hours ago", icon: <FaBriefcase /> },
    { id: 2, type: "candidate", user: "Dev Patel", action: "Moved to Interview stage", target: "Priya Sharma", time: "3 hours ago", icon: <FaUser /> },
    { id: 3, type: "candidate", user: "Anna Kovac", action: "Left a note on", target: "Marcus Dupont", time: "4 hours ago", icon: <FaUser /> },
    { id: 4, type: "security", user: "System", action: "New login detected for", target: "Dev Patel", time: "5 hours ago", icon: <FaShieldAlt /> },
    { id: 5, type: "recruitment", user: "Sarah Jenkins", action: "Closed campaign", target: "Product Designer (UX/UI)", time: "6 hours ago", icon: <FaBriefcase /> },
    { id: 6, type: "system", user: "System", action: "Completed scheduled backup", target: "All databases", time: "7 hours ago", icon: <FaCog /> },
    { id: 7, type: "candidate", user: "Marcus Vance", action: "Shortlisted", target: "Lukas Müller", time: "8 hours ago", icon: <FaUser /> },
    { id: 8, type: "recruitment", user: "Dev Patel", action: "Updated job description for", target: "Senior AI Scientist", time: "9 hours ago", icon: <FaBriefcase /> },
    { id: 9, type: "security", user: "System", action: "Password changed for", target: "Sarah Jenkins", time: "10 hours ago", icon: <FaShieldAlt /> },
    { id: 10, type: "candidate", user: "Elena Rostova", action: "Moved to Rejected", target: "Nathan Drake", time: "11 hours ago", icon: <FaUser /> },
    { id: 11, type: "recruitment", user: "Sarah Jenkins", action: "Published", target: "Growth Marketing Manager campaign", time: "1 day ago", icon: <FaBriefcase /> },
    { id: 12, type: "candidate", user: "Barry Allen", action: "Scheduled AI interview for", target: "Aisha Diallo", time: "1 day ago", icon: <FaUser /> },
    { id: 13, type: "system", user: "System", action: "AI model upgraded to", target: "IntelliGPT-4.5", time: "1 day ago", icon: <FaCog /> },
    { id: 14, type: "security", user: "Dev Patel", action: "Generated new API key for", target: "Slack Integration", time: "2 days ago", icon: <FaShieldAlt /> },
    { id: 15, type: "candidate", user: "Sarah Jenkins", action: "Extended offer to", target: "Lukas Müller", time: "2 days ago", icon: <FaUser /> },
];

const TYPE_META = {
    recruitment: { color: "#6366F1", bg: "rgba(99,102,241,0.12)" },
    candidate:   { color: "#10B981", bg: "rgba(16,185,129,0.12)" },
    system:      { color: "#F59E0B", bg: "rgba(245,158,11,0.12)" },
    security:    { color: "#EF4444", bg: "rgba(239,68,68,0.12)" },
};

const FILTER_TYPES = ["All", "recruitment", "candidate", "system", "security"];

export default function Activity() {
    const [filter, setFilter] = useState("All");
    const [search, setSearch] = useState("");

    const filtered = ACTIVITY_LOG.filter(a => {
        const matchType = filter === "All" || a.type === filter;
        const matchSearch = search === "" ||
            a.action.toLowerCase().includes(search.toLowerCase()) ||
            a.target.toLowerCase().includes(search.toLowerCase()) ||
            a.user.toLowerCase().includes(search.toLowerCase());
        return matchType && matchSearch;
    });

    return (
        <div style={{ display: "flex", flexDirection: "column", gap: 28, animation: "fadeInPage 0.4s ease-out" }}>
            <style>{`@keyframes fadeInPage { from { opacity:0; transform:translateY(12px);} to {opacity:1; transform:translateY(0);}}`}</style>

            <PageHeader
                title="Activity Timeline"
                subtitle="Complete log of all team actions and system events."
                icon={<FaHistory />}
            />

            {/* Filters */}
            <div style={{ display: "flex", gap: 12, flexWrap: "wrap", alignItems: "center" }}>
                <div style={{ position: "relative", display: "flex", alignItems: "center" }}>
                    <FaSearch style={{ position: "absolute", left: 12, color: "var(--text-secondary)", fontSize: 12 }} />
                    <input
                        type="text"
                        placeholder="Search activity..."
                        value={search}
                        onChange={e => setSearch(e.target.value)}
                        style={{
                            paddingLeft: 32, paddingRight: 14, paddingTop: 9, paddingBottom: 9,
                            border: "1px solid var(--border)", borderRadius: "var(--radius-sm)",
                            background: "var(--card)", color: "var(--text)", fontSize: 13,
                            outline: "none", width: 220
                        }}
                    />
                </div>

                <FaFilter style={{ color: "var(--text-secondary)", fontSize: 12 }} />
                {FILTER_TYPES.map(f => {
                    const meta = TYPE_META[f];
                    return (
                        <button
                            key={f}
                            onClick={() => setFilter(f)}
                            style={{
                                padding: "7px 16px",
                                borderRadius: 999,
                                border: `1px solid ${filter === f && meta ? meta.color : "var(--border)"}`,
                                background: filter === f && meta ? meta.bg : "transparent",
                                color: filter === f && meta ? meta.color : filter === f ? "var(--primary)" : "var(--text-secondary)",
                                fontSize: 12, fontWeight: 600, cursor: "pointer",
                                transition: "all 0.2s",
                                ...(filter === f && !meta ? { background: "rgba(59,130,246,0.1)", color: "#3B82F6", borderColor: "#3B82F6" } : {})
                            }}
                        >
                            {f === "All" ? "All Events" : f.charAt(0).toUpperCase() + f.slice(1)}
                        </button>
                    );
                })}
            </div>

            {/* Timeline */}
            <motion.div
                style={{
                    background: "var(--card)", border: "1px solid var(--border)",
                    borderRadius: "var(--radius-md)", padding: "24px",
                    boxShadow: "var(--shadow)"
                }}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2 }}
            >
                <div style={{ display: "flex", flexDirection: "column", gap: 0 }}>
                    {filtered.map((event, i) => {
                        const meta = TYPE_META[event.type] || TYPE_META.system;
                        return (
                            <motion.div
                                key={event.id}
                                initial={{ opacity: 0, x: -10 }}
                                animate={{ opacity: 1, x: 0 }}
                                transition={{ delay: i * 0.04 }}
                                style={{
                                    display: "flex", gap: 16, alignItems: "flex-start",
                                    paddingBottom: i < filtered.length - 1 ? 20 : 0,
                                    cursor: "default"
                                }}
                            >
                                {/* Icon + line */}
                                <div style={{ display: "flex", flexDirection: "column", alignItems: "center", flexShrink: 0 }}>
                                    <div style={{
                                        width: 36, height: 36, borderRadius: "var(--radius-sm)",
                                        background: meta.bg, color: meta.color,
                                        display: "flex", alignItems: "center", justifyContent: "center",
                                        fontSize: 14
                                    }}>
                                        {event.icon}
                                    </div>
                                    {i < filtered.length - 1 && (
                                        <div style={{
                                            width: 1, flex: 1, background: "rgba(255,255,255,0.06)",
                                            marginTop: 6, minHeight: 16
                                        }} />
                                    )}
                                </div>

                                {/* Content */}
                                <div style={{ flex: 1, paddingTop: 6 }}>
                                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                                        <p style={{ fontSize: 13, color: "var(--text)", lineHeight: 1.5 }}>
                                            <strong style={{ color: meta.color }}>{event.user}</strong>
                                            {" "}{event.action}{" "}
                                            <strong style={{ color: "var(--text)" }}>{event.target}</strong>
                                        </p>
                                        <span style={{ fontSize: 11, color: "var(--text-secondary)", flexShrink: 0, marginLeft: 16, marginTop: 2 }}>
                                            {event.time}
                                        </span>
                                    </div>
                                </div>
                            </motion.div>
                        );
                    })}

                    {filtered.length === 0 && (
                        <div style={{ textAlign: "center", padding: 40, color: "var(--text-secondary)" }}>
                            <FaHistory style={{ fontSize: 28, marginBottom: 12, opacity: 0.3 }} />
                            <p>No activity matches your search or filter.</p>
                        </div>
                    )}
                </div>
            </motion.div>
        </div>
    );
}