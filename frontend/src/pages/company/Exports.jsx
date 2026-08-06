import React, { useState, useEffect } from "react";
import { motion } from "framer-motion";
import {
    FaDownload, FaFileExcel, FaFilePdf, FaFileCsv,
    FaUsers, FaBriefcase, FaCalendarAlt, FaChartBar,
    FaCheck, FaTrash, FaSpinner
} from "react-icons/fa";

import PageHeader from "../../components/common/PageHeader";
import Button from "../../components/common/Button";
import Toast from "../../components/common/Toast";
import StatusBadge from "../../components/common/StatusBadge";
import FeatureGuard from "../../components/common/FeatureGuard";
import exportService from "../../services/company/exportService";

const EXPORT_TYPES = [
    {
        id: "candidates",
        typeKey: "candidates",
        title: "Candidate Data",
        desc: "All candidate profiles, scores, and status",
        icon: <FaUsers />,
        color: "#3B82F6",
        bg: "rgba(59,130,246,0.12)",
        formats: ["CSV", "Excel", "PDF"]
    },
    {
        id: "jobs",
        typeKey: "jobs",
        title: "Job Listings",
        desc: "All open, paused and closed job roles",
        icon: <FaBriefcase />,
        color: "#10B981",
        bg: "rgba(16,185,129,0.12)",
        formats: ["CSV", "Excel"]
    },
    {
        id: "interviews",
        typeKey: "interviews",
        title: "Interview Records",
        desc: "Scheduled and completed interview logs",
        icon: <FaCalendarAlt />,
        color: "#8B5CF6",
        bg: "rgba(139,92,246,0.12)",
        formats: ["CSV", "PDF"]
    },
    {
        id: "analytics",
        typeKey: "analytics",
        title: "Analytics Report",
        desc: "Hiring funnel, KPIs and sourcing data",
        icon: <FaChartBar />,
        color: "#F59E0B",
        bg: "rgba(245,158,11,0.12)",
        formats: ["PDF", "Excel"]
    },
];

const FORMAT_ICONS = {
    CSV: <FaFileCsv style={{ color: "#F59E0B" }} />,
    Excel: <FaFileExcel style={{ color: "#10B981" }} />,
    PDF: <FaFilePdf style={{ color: "#EF4444" }} />,
};

export default function Exports() {
    const [counts, setCounts] = useState({ candidates: 1038, jobs: 15, interviews: 382, analytics: "Full report" });
    const [history, setHistory] = useState([]);
    const [loading, setLoading] = useState(true);
    const [exporting, setExporting] = useState({});
    const [done, setDone] = useState({});
    const [selectedFormats, setSelectedFormats] = useState(
        Object.fromEntries(EXPORT_TYPES.map(e => [e.id, e.formats[0]]))
    );
    const [toast, setToast] = useState(null);

    const showToast = (message, type = "success") => {
        setToast({ message, type });
    };

    const loadData = async () => {
        try {
            setLoading(true);
            const [countsRes, historyRes] = await Promise.all([
                exportService.getSummaryCounts(),
                exportService.getHistory()
            ]);
            setCounts(countsRes.data || {});
            setHistory(historyRes.data || []);
        } catch (err) {
            console.error("Error loading export data:", err);
            showToast("Failed to load export data from backend", "error");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        loadData();
    }, []);

    const handleExport = async (exp) => {
        const fmt = selectedFormats[exp.id] || "CSV";
        try {
            setExporting(prev => ({ ...prev, [exp.id]: true }));
            const res = await exportService.createExport({ type: exp.id, format: fmt });
            setDone(prev => ({ ...prev, [exp.id]: true }));
            showToast(`Exported ${exp.title} as ${fmt}`, "success");
            loadData();
            setTimeout(() => setDone(prev => ({ ...prev, [exp.id]: false })), 2500);
        } catch (err) {
            console.error("Export creation failed:", err);
            showToast("Failed to create export", "error");
        } finally {
            setExporting(prev => ({ ...prev, [exp.id]: false }));
        }
    };

    const handleDownload = async (item) => {
        try {
            const res = await exportService.downloadExport(item.id);
            const blob = new Blob([res.data], { type: res.headers["content-type"] || "text/csv" });
            const url = window.URL.createObjectURL(blob);
            const link = document.createElement("a");
            link.href = url;
            link.setAttribute("download", item.file_name || `export_${item.id}.${item.format.toLowerCase()}`);
            document.body.appendChild(link);
            link.click();
            link.remove();
            window.URL.revokeObjectURL(url);
            showToast(`Downloaded ${item.title}`, "success");
        } catch (err) {
            console.error("Download failed:", err);
            showToast("Failed to download export file", "error");
        }
    };

    const handleDelete = async (exportId) => {
        try {
            await exportService.deleteExport(exportId);
            showToast("Export record deleted", "success");
            loadData();
        } catch (err) {
            console.error("Delete export failed:", err);
            showToast("Failed to delete export record", "error");
        }
    };

    return (
        <FeatureGuard featureName="export_reports">
            <div style={{ display: "flex", flexDirection: "column", gap: 32, animation: "fadeInPage 0.4s ease-out" }}>
                {toast && (
                <Toast
                    message={toast.message}
                    type={toast.type}
                    onClose={() => setToast(null)}
                />
            )}

            <PageHeader
                title="Exports"
                subtitle="Download your recruitment data in various formats for offline analysis."
                icon={<FaDownload />}
            />

            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))", gap: 20 }}>
                {EXPORT_TYPES.map((exp, i) => {
                    const recordLabel = counts[exp.typeKey]
                        ? (typeof counts[exp.typeKey] === "number" ? `${counts[exp.typeKey]} records` : counts[exp.typeKey])
                        : "Available";

                    return (
                        <motion.div
                            key={exp.id}
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: i * 0.1 }}
                            style={{
                                background: "var(--card)",
                                border: "1px solid var(--border)",
                                borderRadius: "var(--radius-md)",
                                padding: "24px",
                                boxShadow: "var(--shadow)",
                                display: "flex",
                                flexDirection: "column",
                                gap: 16
                            }}
                        >
                            {/* Header */}
                            <div style={{ display: "flex", alignItems: "flex-start", gap: 14 }}>
                                <div style={{
                                    width: 48, height: 48, borderRadius: "var(--radius-sm)",
                                    background: exp.bg, color: exp.color,
                                    display: "flex", alignItems: "center", justifyContent: "center",
                                    fontSize: 20, flexShrink: 0
                                }}>
                                    {exp.icon}
                                </div>
                                <div>
                                    <h4 style={{ fontSize: 15, fontWeight: 700, color: "var(--text)", marginBottom: 4 }}>{exp.title}</h4>
                                    <p style={{ fontSize: 12.5, color: "var(--text-secondary)" }}>{exp.desc}</p>
                                </div>
                            </div>

                            {/* Record count */}
                            <div style={{
                                padding: "8px 14px",
                                background: "rgba(255,255,255,0.04)",
                                borderRadius: "var(--radius-sm)",
                                border: "1px solid var(--border)",
                                fontSize: 12,
                                color: "var(--text-secondary)",
                                display: "flex",
                                justifyContent: "space-between"
                            }}>
                                <span>Available Records</span>
                                <strong style={{ color: "var(--text)" }}>{recordLabel}</strong>
                            </div>

                            {/* Format selection */}
                            <div>
                                <p style={{ fontSize: 11, fontWeight: 600, color: "var(--text-secondary)", marginBottom: 8, textTransform: "uppercase", letterSpacing: "0.5px" }}>
                                    Export Format
                                </p>
                                <div style={{ display: "flex", gap: 8 }}>
                                    {exp.formats.map(fmt => (
                                        <button
                                            key={fmt}
                                            onClick={() => setSelectedFormats(prev => ({ ...prev, [exp.id]: fmt }))}
                                            style={{
                                                display: "flex", alignItems: "center", gap: 6,
                                                padding: "7px 14px",
                                                borderRadius: "var(--radius-sm)",
                                                border: `1px solid ${selectedFormats[exp.id] === fmt ? exp.color : "var(--border)"}`,
                                                background: selectedFormats[exp.id] === fmt ? `${exp.bg}` : "transparent",
                                                color: selectedFormats[exp.id] === fmt ? exp.color : "var(--text-secondary)",
                                                fontSize: 12, fontWeight: 600, cursor: "pointer",
                                                transition: "all 0.2s"
                                            }}
                                        >
                                            {FORMAT_ICONS[fmt]}
                                            {fmt}
                                        </button>
                                    ))}
                                </div>
                            </div>

                            {/* Export button */}
                            <Button
                                variant={done[exp.id] ? "outline" : "primary"}
                                icon={done[exp.id] ? <FaCheck /> : exporting[exp.id] ? null : <FaDownload />}
                                onClick={() => handleExport(exp)}
                                disabled={exporting[exp.id]}
                            >
                                {done[exp.id] ? "Downloaded!" : exporting[exp.id] ? "Preparing..." : `Export as ${selectedFormats[exp.id]}`}
                            </Button>
                        </motion.div>
                    );
                })}
            </div>

            {/* Export History Table */}
            <div style={{
                background: "var(--card)",
                border: "1px solid var(--border)",
                borderRadius: "var(--radius-lg)",
                padding: "24px",
                display: "flex",
                flexDirection: "column",
                gap: 16
            }}>
                <h4 style={{ fontSize: 16, fontWeight: 700, color: "var(--text)" }}>Export History</h4>

                {loading ? (
                    <div style={{ display: "flex", justifyContent: "center", alignItems: "center", padding: "40px", gap: 12, color: "var(--text-secondary)" }}>
                        <FaSpinner className="animate-spin" style={{ fontSize: 18 }} />
                        <span>Loading export history from backend...</span>
                    </div>
                ) : (
                    <div style={{ overflowX: "auto" }}>
                        <table className="data-table" style={{ width: "100%", borderCollapse: "collapse" }}>
                            <thead>
                                <tr style={{ textAlign: "left", borderBottom: "1px solid var(--border)", color: "var(--text-secondary)", fontSize: 12 }}>
                                    <th style={{ padding: "12px 16px" }}>Export Title</th>
                                    <th style={{ padding: "12px 16px" }}>Format</th>
                                    <th style={{ padding: "12px 16px" }}>Records</th>
                                    <th style={{ padding: "12px 16px" }}>Size</th>
                                    <th style={{ padding: "12px 16px" }}>Created Date</th>
                                    <th style={{ padding: "12px 16px" }}>Status</th>
                                    <th style={{ padding: "12px 16px" }}>Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                {history.map(item => (
                                    <tr key={item.id} style={{ borderBottom: "1px solid var(--border)", fontSize: 13, color: "var(--text)" }}>
                                        <td style={{ padding: "12px 16px", fontWeight: 600 }}>{item.title}</td>
                                        <td style={{ padding: "12px 16px" }}>
                                            <span style={{ display: "inline-flex", alignItems: "center", gap: 6 }}>
                                                {FORMAT_ICONS[item.format]} {item.format}
                                            </span>
                                        </td>
                                        <td style={{ padding: "12px 16px", color: "var(--text-secondary)" }}>{item.records}</td>
                                        <td style={{ padding: "12px 16px", color: "var(--text-secondary)" }}>{item.size}</td>
                                        <td style={{ padding: "12px 16px", color: "var(--text-secondary)" }}>{item.created_at}</td>
                                        <td style={{ padding: "12px 16px" }}>
                                            <StatusBadge status={item.status} />
                                        </td>
                                        <td style={{ padding: "12px 16px" }}>
                                            <div style={{ display: "flex", gap: 8 }}>
                                                <button
                                                    onClick={() => handleDownload(item)}
                                                    title="Download File"
                                                    style={{ background: "transparent", border: "none", color: "var(--primary)", cursor: "pointer", fontSize: 14 }}
                                                >
                                                    <FaDownload />
                                                </button>
                                                <button
                                                    onClick={() => handleDelete(item.id)}
                                                    title="Delete Export"
                                                    style={{ background: "transparent", border: "none", color: "var(--danger, #EF4444)", cursor: "pointer", fontSize: 14 }}
                                                >
                                                    <FaTrash />
                                                </button>
                                            </div>
                                        </td>
                                    </tr>
                                ))}
                                {history.length === 0 && (
                                    <tr>
                                        <td colSpan={7} style={{ textAlign: "center", padding: "30px", color: "var(--text-secondary)" }}>
                                            No export history found.
                                        </td>
                                    </tr>
                                )}
                            </tbody>
                        </table>
                    </div>
                )}
                </div>
            </div>
        </FeatureGuard>
    );
}