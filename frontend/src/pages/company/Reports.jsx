import React, { useState, useEffect } from "react";
import { motion } from "framer-motion";
import {
    FaFileAlt, FaDownload, FaEye, FaTrash,
    FaFileExcel, FaFilePdf, FaFileCsv,
    FaChartBar, FaUsers, FaBriefcase, FaShieldAlt,
    FaPlus, FaSearch, FaSpinner
} from "react-icons/fa";

import PageHeader from "../../components/common/PageHeader";
import Button from "../../components/common/Button";
import StatusBadge from "../../components/common/StatusBadge";
import Toast from "../../components/common/Toast";
import reportService from "../../services/company/reportService";

import "../../styles/company/Reports.css";

const REPORT_TYPES = [
    {
        id: "hiring",
        label: "Hiring Report",
        desc: "Applications, funnel, selections",
        icon: <FaChartBar />,
        color: "#3B82F6",
        bg: "rgba(59,130,246,0.12)"
    },
    {
        id: "candidate",
        label: "Candidate Report",
        desc: "Profiles, scores, shortlists",
        icon: <FaUsers />,
        color: "#10B981",
        bg: "rgba(16,185,129,0.12)"
    },
    {
        id: "department",
        label: "Dept. Report",
        desc: "Per-department headcount",
        icon: <FaBriefcase />,
        color: "#8B5CF6",
        bg: "rgba(139,92,246,0.12)"
    },
    {
        id: "recruiter",
        label: "Recruiter Report",
        desc: "Performance scorecards",
        icon: <FaFileAlt />,
        color: "#F59E0B",
        bg: "rgba(245,158,11,0.12)"
    },
    {
        id: "security",
        label: "Security Report",
        desc: "Audit & compliance logs",
        icon: <FaShieldAlt />,
        color: "#EC4899",
        bg: "rgba(236,72,153,0.12)"
    },
];

const FORMAT_ICON_MAP = {
    PDF: { label: "PDF", cls: "pdf" },
    Excel: { label: "XLS", cls: "excel" },
    CSV: { label: "CSV", cls: "csv" },
};

const cardVariants = {
    hidden: { opacity: 0, y: 16 },
    visible: (i) => ({ opacity: 1, y: 0, transition: { delay: i * 0.07, duration: 0.35 } })
};

export default function Reports() {
    const [reports, setReports] = useState([]);
    const [loading, setLoading] = useState(true);
    const [selectedType, setSelectedType] = useState(null);
    const [searchTerm, setSearchTerm] = useState("");
    const [generating, setGenerating] = useState(false);
    const [genForm, setGenForm] = useState({ type: "hiring", period: "last_month", format: "PDF" });
    const [toast, setToast] = useState(null);

    const showToast = (message, type = "success") => {
        setToast({ message, type });
    };

    const fetchReports = async () => {
        try {
            setLoading(true);
            const typeFilter = selectedType || "";
            const res = await reportService.getReports(typeFilter, searchTerm);
            setReports(res.data || []);
        } catch (err) {
            console.error("Error loading reports:", err);
            showToast("Failed to load reports from backend", "error");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchReports();
    }, [selectedType, searchTerm]);

    const handleGenerate = async () => {
        try {
            setGenerating(true);
            await reportService.generateReport(genForm);
            showToast("Report generated successfully!", "success");
            fetchReports();
        } catch (err) {
            console.error("Report generation failed:", err);
            showToast("Failed to generate report", "error");
        } finally {
            setGenerating(false);
        }
    };

    const handleDownload = async (report) => {
        try {
            const res = await reportService.downloadReport(report.id);
            const blob = new Blob([res.data], { type: res.headers["content-type"] || "application/pdf" });
            const url = window.URL.createObjectURL(blob);
            const link = document.createElement("a");
            link.href = url;
            const ext = (report.format || "pdf").toLowerCase();
            link.setAttribute("download", `${report.name.replace(/\s+/g, "_")}.${ext}`);
            document.body.appendChild(link);
            link.click();
            link.remove();
            window.URL.revokeObjectURL(url);
            showToast(`Downloaded ${report.name}`, "success");
            fetchReports();
        } catch (err) {
            console.error("Download failed:", err);
            showToast("Failed to download report file", "error");
        }
    };

    const handleDelete = async (reportId) => {
        try {
            await reportService.deleteReport(reportId);
            showToast("Report deleted successfully", "success");
            fetchReports();
        } catch (err) {
            console.error("Delete failed:", err);
            showToast("Failed to delete report", "error");
        }
    };

    return (
        <div className="reports-page">
            {toast && (
                <Toast
                    message={toast.message}
                    type={toast.type}
                    onClose={() => setToast(null)}
                />
            )}

            <PageHeader
                title="Reports"
                subtitle="Manage and export hiring reports."
                icon={<FaFileAlt />}
                actions={
                    <Button variant="primary" icon={<FaPlus />} size="sm" onClick={handleGenerate} disabled={generating}>
                        {generating ? "Generating..." : "New Report"}
                    </Button>
                }
            />

            {/* Report Type Filter Cards */}
            <div className="report-type-grid">
                {REPORT_TYPES.map((rt, i) => (
                    <motion.div
                        key={rt.id}
                        className={`report-type-card ${selectedType === rt.id ? "selected" : ""}`}
                        custom={i}
                        variants={cardVariants}
                        initial="hidden"
                        animate="visible"
                        onClick={() => setSelectedType(prev => prev === rt.id ? null : rt.id)}
                    >
                        <div className="report-type-icon" style={{ background: rt.bg, color: rt.color }}>
                            {rt.icon}
                        </div>
                        <div>
                            <h5>{rt.label}</h5>
                            <p>{rt.desc}</p>
                        </div>
                    </motion.div>
                ))}
            </div>

            {/* Main Body */}
            <div className="reports-body">
                {/* Reports Table */}
                <motion.div
                    className="report-panel"
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.3 }}
                >
                    <div className="report-panel-header">
                        <div>
                            <h4>All Reports</h4>
                            <p>{reports.length} report{reports.length !== 1 ? "s" : ""} available</p>
                        </div>
                        <div className="report-panel-actions">
                            <div style={{ position: "relative", display: "flex", alignItems: "center" }}>
                                <FaSearch style={{ position: "absolute", left: 10, color: "var(--text-secondary)", fontSize: 12 }} />
                                <input
                                    type="text"
                                    placeholder="Search reports..."
                                    value={searchTerm}
                                    onChange={e => setSearchTerm(e.target.value)}
                                    style={{
                                        paddingLeft: 30, paddingRight: 12, paddingTop: 8, paddingBottom: 8,
                                        border: "1px solid var(--border)", borderRadius: "var(--radius-sm)",
                                        background: "rgba(255,255,255,0.04)", color: "var(--text)",
                                        fontSize: 13, outline: "none", width: 200
                                    }}
                                />
                            </div>
                        </div>
                    </div>

                    <div className="reports-table-wrap">
                        {loading ? (
                            <div style={{ display: "flex", justifyContent: "center", alignItems: "center", padding: "60px", gap: 12, color: "var(--text-secondary)" }}>
                                <FaSpinner className="animate-spin" style={{ fontSize: 20 }} />
                                <span>Loading report data from backend...</span>
                            </div>
                        ) : (
                            <table className="reports-list-table">
                                <thead>
                                    <tr>
                                        <th>Report Name</th>
                                        <th>Type</th>
                                        <th>Generated By</th>
                                        <th>Date</th>
                                        <th>Size</th>
                                        <th>Status</th>
                                        <th>Actions</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {reports.map((report, i) => {
                                        const fmtKey = (report.format || "PDF").toUpperCase();
                                        const fmt = FORMAT_ICON_MAP[fmtKey] || { label: fmtKey, cls: "pdf" };
                                        return (
                                            <motion.tr
                                                key={report.id}
                                                initial={{ opacity: 0 }}
                                                animate={{ opacity: 1 }}
                                                transition={{ delay: 0.05 * i }}
                                            >
                                                <td>
                                                    <div className="report-name-cell">
                                                        <div className={`report-format-icon ${fmt.cls}`}>
                                                            {fmt.label}
                                                        </div>
                                                        <div className="report-name-text">
                                                            <strong>{report.name}</strong>
                                                            <span>Downloaded {report.downloadCount || 0}×</span>
                                                        </div>
                                                    </div>
                                                </td>
                                                <td style={{ color: "var(--text-secondary)", fontSize: 12 }}>{report.type}</td>
                                                <td>
                                                    <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                                                        <div style={{
                                                            width: 26, height: 26, borderRadius: "50%",
                                                            background: "var(--primary)", color: "#fff",
                                                            fontSize: 10, fontWeight: 700, display: "flex",
                                                            alignItems: "center", justifyContent: "center"
                                                        }}>
                                                            {(report.generatedBy || "Admin").split(" ").map(n => n[0]).join("").slice(0, 2)}
                                                        </div>
                                                        {report.generatedBy || "Admin"}
                                                    </div>
                                                </td>
                                                <td style={{ color: "var(--text-secondary)", fontSize: 12 }}>
                                                    {report.date}
                                                </td>
                                                <td style={{ color: "var(--text-secondary)", fontSize: 12 }}>{report.size}</td>
                                                <td>
                                                    <StatusBadge status={report.status} />
                                                </td>
                                                <td>
                                                    <div className="report-actions-cell">
                                                        <button className="report-icon-btn" title="Download" onClick={() => handleDownload(report)}><FaDownload /></button>
                                                        <button className="report-icon-btn" title="Delete" onClick={() => handleDelete(report.id)}><FaTrash /></button>
                                                    </div>
                                                </td>
                                            </motion.tr>
                                        );
                                    })}
                                    {reports.length === 0 && (
                                        <tr>
                                            <td colSpan={7} style={{ textAlign: "center", padding: "40px", color: "var(--text-secondary)" }}>
                                                No reports match your filter.
                                            </td>
                                        </tr>
                                    )}
                                </tbody>
                            </table>
                        )}
                    </div>
                </motion.div>

                {/* Sidebar */}
                <div className="report-sidebar-panel">
                    {/* Generate Report */}
                    <motion.div
                        className="generate-report-card"
                        initial={{ opacity: 0, x: 20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: 0.35 }}
                    >
                        <h4>Generate New Report</h4>
                        <div className="generate-report-form">
                            <div className="generate-form-group">
                                <label>Report Type</label>
                                <select value={genForm.type} onChange={e => setGenForm(f => ({ ...f, type: e.target.value }))}>
                                    <option value="hiring">Hiring Report</option>
                                    <option value="candidate">Candidate Report</option>
                                    <option value="department">Department Report</option>
                                    <option value="recruiter">Recruiter Report</option>
                                    <option value="security">Security Report</option>
                                </select>
                            </div>
                            <div className="generate-form-group">
                                <label>Time Period</label>
                                <select value={genForm.period} onChange={e => setGenForm(f => ({ ...f, period: e.target.value }))}>
                                    <option value="last_month">Last Month</option>
                                    <option value="last_quarter">Last Quarter</option>
                                    <option value="last_6months">Last 6 Months</option>
                                    <option value="ytd">Year to Date</option>
                                    <option value="custom">Custom Range</option>
                                </select>
                            </div>
                            <div className="generate-form-group">
                                <label>Format</label>
                                <select value={genForm.format} onChange={e => setGenForm(f => ({ ...f, format: e.target.value }))}>
                                    <option value="PDF">PDF</option>
                                    <option value="Excel">Excel (.xlsx)</option>
                                    <option value="CSV">CSV</option>
                                </select>
                            </div>
                            <Button
                                variant="primary"
                                onClick={handleGenerate}
                                disabled={generating}
                            >
                                {generating ? "Generating..." : "Generate Report"}
                            </Button>
                        </div>
                    </motion.div>

                    {/* Recent Generated Activity */}
                    <motion.div
                        className="history-panel"
                        initial={{ opacity: 0, x: 20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: 0.45 }}
                    >
                        <h4>Recent System Reports</h4>
                        {reports.slice(0, 5).map((item) => {
                            const fmtKey = (item.format || "PDF").toUpperCase();
                            const fmt = FORMAT_ICON_MAP[fmtKey] || { label: fmtKey, cls: "pdf" };
                            return (
                                <div key={item.id} className="history-item">
                                    <div className={`report-format-icon ${fmt.cls}`} style={{ width: 32, height: 32, fontSize: 9 }}>
                                        {fmt.label}
                                    </div>
                                    <div className="history-text">
                                        <strong>{item.name}</strong>
                                        <span>{item.date} · {item.size}</span>
                                    </div>
                                    <button className="history-dl-btn" title="Download" onClick={() => handleDownload(item)}>
                                        <FaDownload />
                                    </button>
                                </div>
                            );
                        })}
                    </motion.div>
                </div>
            </div>
        </div>
    );
}
