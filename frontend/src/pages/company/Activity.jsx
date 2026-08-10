import React, { useState } from "react";
import { motion } from "framer-motion";
import {
    FaHistory, FaBriefcase, FaUser, FaCog, FaShieldAlt,
    FaSearch, FaFilter
} from "react-icons/fa";

import PageHeader from "../../components/common/PageHeader";

import auditLogService from "../../services/company/auditLogService";

const TYPE_META = {
    recruitment: { color: "#6366F1", bg: "rgba(99,102,241,0.12)", icon: <FaBriefcase /> },
    candidate:   { color: "#10B981", bg: "rgba(16,185,129,0.12)", icon: <FaUser /> },
    system:      { color: "#F59E0B", bg: "rgba(245,158,11,0.12)", icon: <FaCog /> },
    security:    { color: "#EF4444", bg: "rgba(239,68,68,0.12)", icon: <FaShieldAlt /> },
};


const FILTER_TYPES = ["All", "recruitment", "candidate", "system", "security"];

export default function Activity() {
    const [filter, setFilter] = useState("All");
    const [search, setSearch] = useState("");

    const [logs, setLogs] = React.useState([]);
    const [loading, setLoading] = React.useState(true);

    React.useEffect(() => {
        const fetchLogs = async () => {
            try {
                setLoading(true);
                const res = await auditLogService.getLogs();
                setLogs(res.data || []);
            } catch (err) {
                console.error("Failed to fetch logs:", err);
            } finally {
                setLoading(false);
            }
        };
        fetchLogs();
    }, []);

    const filtered = logs.filter(a => {
        const matchType = filter === "All" || a.type === filter;
        const matchSearch = search === "" ||
            a.action?.toLowerCase().includes(search.toLowerCase()) ||
            a.target?.toLowerCase().includes(search.toLowerCase()) ||
            a.user?.toLowerCase().includes(search.toLowerCase());
        return matchType && matchSearch;
    });

    if (loading) {
        return <div style={{ padding: 40, textAlign: "center", color: "var(--text-secondary)" }}>Loading activity logs...</div>;
    }

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
                                        width: 40, height: 40, borderRadius: "50%",
                                        background: meta.bg, color: meta.color,
                                        display: "flex", alignItems: "center", justifyContent: "center",
                                        fontSize: 16
                                    }}>
                                        {meta.icon}
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
                                        <span style={{ fontSize: 13, color: "var(--text-secondary)" }}>
                                            {event.time ? new Date(event.time).toLocaleString() : "Recently"}
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