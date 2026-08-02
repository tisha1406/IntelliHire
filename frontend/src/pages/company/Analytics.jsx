import React, { useState, useEffect } from "react";
import {
    Chart as ChartJS,
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    BarElement,
    ArcElement,
    Tooltip,
    Legend,
    Filler,
} from "chart.js";
import { Line, Bar, Doughnut } from "react-chartjs-2";
import { motion } from "framer-motion";
import {
    FaChartLine,
    FaUsers,
    FaClock,
    FaHandshake,
    FaCheckCircle,
    FaDownload,
    FaFilter,
    FaSpinner,
} from "react-icons/fa";

import PageHeader from "../../components/common/PageHeader";
import Button from "../../components/common/Button";
import StatsCard from "../../components/common/StatsCard";
import analyticsService from "../../services/company/analyticsService";

import "../../styles/company/Analytics.css";

ChartJS.register(
    CategoryScale, LinearScale, PointElement, LineElement,
    BarElement, ArcElement, Tooltip, Legend, Filler
);

const cardVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: (i) => ({ opacity: 1, y: 0, transition: { delay: i * 0.08, duration: 0.4 } })
};

const FUNNEL_COLORS = [
    "#3B82F6", "#6366F1", "#8B5CF6", "#A855F7", "#D946EF", "#EC4899"
];

const periodFilters = ["This Month", "Last 3 Months", "Last 6 Months", "This Year"];

const CHART_TOOLTIP = {
    backgroundColor: "rgba(10,17,38,0.95)",
    borderColor: "rgba(59,130,246,0.3)",
    borderWidth: 1,
    titleColor: "#fff",
    bodyColor: "#94A3B8",
    padding: 12,
};

export default function Analytics() {
    const [activePeriod, setActivePeriod] = useState("This Year");
    const [loading, setLoading] = useState(true);

    const [kpis, setKpis] = useState(null);
    const [hiringTrend, setHiringTrend] = useState([]);
    const [candidateSources, setCandidateSources] = useState([]);
    const [hiringFunnel, setHiringFunnel] = useState([]);
    const [departmentData, setDepartmentData] = useState([]);
    const [recruiterData, setRecruiterData] = useState([]);
    const [yearlyComparison, setYearlyComparison] = useState([]);

    useEffect(() => {
        const loadAll = async () => {
            setLoading(true);
            try {
                const [
                    kpiRes,
                    trendRes,
                    sourcesRes,
                    funnelRes,
                    deptRes,
                    recruiterRes,
                    yearlyRes,
                ] = await Promise.all([
                    analyticsService.getKPIs(),
                    analyticsService.getHiringTrend(),
                    analyticsService.getCandidateSources(),
                    analyticsService.getHiringFunnel(),
                    analyticsService.getDepartmentBreakdown(),
                    analyticsService.getRecruiterPerformance(),
                    analyticsService.getYearlyComparison(),
                ]);

                setKpis(kpiRes.data);
                setHiringTrend(trendRes.data || []);
                setCandidateSources(sourcesRes.data || []);
                setHiringFunnel(funnelRes.data || []);
                setDepartmentData(deptRes.data || []);
                setRecruiterData(recruiterRes.data || []);
                setYearlyComparison(yearlyRes.data || []);
            } catch (err) {
                console.error("Failed to load analytics data:", err);
            } finally {
                setLoading(false);
            }
        };
        loadAll();
    }, [activePeriod]);

    // ─── KPI Cards ─────────────────────────────────────────────────────────────
    const kpiCards = kpis
        ? [
            { label: "Avg. Time to Hire", value: kpis.averageTimeToHire?.value, change: kpis.averageTimeToHire?.change, positive: kpis.averageTimeToHire?.positive, icon: <FaClock />, color: "#3B82F6" },
            { label: "Offer Acceptance Rate", value: kpis.offerAcceptanceRate?.value, change: kpis.offerAcceptanceRate?.change, positive: kpis.offerAcceptanceRate?.positive, icon: <FaHandshake />, color: "#10B981" },
            { label: "Total Applications", value: kpis.totalApplications?.value, change: kpis.totalApplications?.change, positive: kpis.totalApplications?.positive, icon: <FaUsers />, color: "#8B5CF6" },
            { label: "Total Interviews", value: kpis.totalInterviews?.value, change: kpis.totalInterviews?.change, positive: kpis.totalInterviews?.positive, icon: <FaChartLine />, color: "#F59E0B" },
            { label: "Selections Made", value: kpis.selections?.value, change: kpis.selections?.change, positive: kpis.selections?.positive, icon: <FaCheckCircle />, color: "#EC4899" },
        ]
        : [];

    // ─── Chart: Hiring Trend ────────────────────────────────────────────────────
    const hiringTrendData = {
        labels: hiringTrend.map(d => d.month),
        datasets: [
            {
                label: "Applications",
                data: hiringTrend.map(d => d.applications),
                borderColor: "#3B82F6",
                backgroundColor: "rgba(59, 130, 246, 0.12)",
                borderWidth: 2.5,
                fill: true,
                tension: 0.4,
                pointRadius: 3,
                pointBackgroundColor: "#3B82F6",
            },
            {
                label: "Selections",
                data: hiringTrend.map(d => d.selections),
                borderColor: "#10B981",
                backgroundColor: "rgba(16, 185, 129, 0.10)",
                borderWidth: 2.5,
                fill: true,
                tension: 0.4,
                pointRadius: 3,
                pointBackgroundColor: "#10B981",
            }
        ]
    };

    const lineChartOptions = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: { display: false },
            tooltip: CHART_TOOLTIP,
        },
        scales: {
            x: {
                grid: { color: "rgba(255,255,255,0.04)" },
                ticks: { color: "#64748B", font: { size: 11 } }
            },
            y: {
                grid: { color: "rgba(255,255,255,0.04)" },
                ticks: { color: "#64748B", font: { size: 11 } }
            }
        }
    };

    // ─── Chart: Doughnut (Sources) ──────────────────────────────────────────────
    const sourceDoughnutData = {
        labels: candidateSources.map(s => s.source),
        datasets: [{
            data: candidateSources.map(s => s.value),
            backgroundColor: candidateSources.map(s => s.color),
            borderWidth: 0,
            borderRadius: 4,
        }]
    };

    const doughnutOptions = {
        responsive: true,
        maintainAspectRatio: false,
        cutout: "72%",
        plugins: {
            legend: { display: false },
            tooltip: CHART_TOOLTIP,
        }
    };

    // ─── Chart: Monthly Comparison Bar ─────────────────────────────────────────
    const comparisonData = {
        labels: yearlyComparison.map(d => d.month),
        datasets: [
            {
                label: "2025",
                data: yearlyComparison.map(d => d.year2025),
                backgroundColor: "rgba(99, 102, 241, 0.7)",
                borderRadius: 6,
                borderSkipped: false,
            },
            {
                label: "2026",
                data: yearlyComparison.map(d => d.year2026),
                backgroundColor: "rgba(59, 130, 246, 0.85)",
                borderRadius: 6,
                borderSkipped: false,
            }
        ]
    };

    const barChartOptions = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: { display: false },
            tooltip: CHART_TOOLTIP,
        },
        scales: {
            x: {
                grid: { display: false },
                ticks: { color: "#64748B", font: { size: 11 } }
            },
            y: {
                grid: { color: "rgba(255,255,255,0.04)" },
                ticks: { color: "#64748B", font: { size: 11 } }
            }
        }
    };

    if (loading) {
        return (
            <div className="analytics-page">
                <PageHeader title="Analytics" subtitle="Hiring insights and performance metrics." icon={<FaChartLine />} />
                <div style={{ display: "flex", justifyContent: "center", alignItems: "center", padding: "80px", gap: 14, color: "var(--text-secondary)" }}>
                    <FaSpinner style={{ fontSize: 22, animation: "spin 1s linear infinite" }} />
                    <span style={{ fontSize: 14 }}>Loading analytics from backend…</span>
                </div>
            </div>
        );
    }

    return (
        <div className="analytics-page">
            <PageHeader
                title="Analytics"
                subtitle="Hiring insights and performance metrics."
                icon={<FaChartLine />}
                actions={
                    <Button variant="outline" icon={<FaDownload />} size="sm">
                        Export Report
                    </Button>
                }
            />

            {/* Period filter chips */}
            <div className="analytics-filter-bar">
                <FaFilter size={12} style={{ color: "var(--text-secondary)" }} />
                {periodFilters.map(p => (
                    <button
                        key={p}
                        className={`filter-chip ${activePeriod === p ? "active" : ""}`}
                        onClick={() => setActivePeriod(p)}
                    >
                        {p}
                    </button>
                ))}
            </div>

            {/* KPI Cards */}
            <div className="analytics-kpi-grid">
                {kpiCards.map((kpi, i) => (
                    <motion.div key={kpi.label} custom={i} variants={cardVariants} initial="hidden" animate="visible">
                        <StatsCard
                            title={kpi.label}
                            value={kpi.value}
                            change={kpi.change}
                            positive={kpi.positive}
                            icon={kpi.icon}
                            iconColor={kpi.color}
                        />
                    </motion.div>
                ))}
            </div>

            {/* Charts — Top Row */}
            <div className="analytics-charts-top">
                {/* Hiring Trend */}
                <motion.div
                    className="analytics-chart-panel"
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.3 }}
                >
                    <div className="chart-panel-header">
                        <div>
                            <h4>Hiring Trend</h4>
                            <p>Monthly applications vs. selections this year</p>
                        </div>
                        <div className="comparison-legend">
                            <div className="legend-item">
                                <div className="legend-dot" style={{ background: "#3B82F6" }} />
                                Applications
                            </div>
                            <div className="legend-item">
                                <div className="legend-dot" style={{ background: "#10B981" }} />
                                Selections
                            </div>
                        </div>
                    </div>
                    <div className="chart-area">
                        <Line data={hiringTrendData} options={lineChartOptions} />
                    </div>
                </motion.div>

                {/* Candidate Sources */}
                <motion.div
                    className="analytics-chart-panel"
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.4 }}
                >
                    <div className="chart-panel-header">
                        <div>
                            <h4>Candidate Sources</h4>
                            <p>Top hiring channels breakdown</p>
                        </div>
                    </div>
                    <div className="chart-area" style={{ height: "180px" }}>
                        <Doughnut data={sourceDoughnutData} options={doughnutOptions} />
                    </div>
                    <div className="source-legend">
                        {candidateSources.map(s => (
                            <div key={s.source}>
                                <div className="source-legend-item">
                                    <div className="source-dot" style={{ background: s.color }} />
                                    <span className="source-name">{s.source}</span>
                                    <span className="source-percent">{s.percentage}%</span>
                                </div>
                                <div className="source-bar">
                                    <div className="source-bar-fill" style={{ width: `${s.percentage}%`, background: s.color }} />
                                </div>
                            </div>
                        ))}
                    </div>
                </motion.div>
            </div>

            {/* Charts — Middle Row */}
            <div className="analytics-charts-mid">
                {/* Hiring Funnel */}
                <motion.div
                    className="analytics-chart-panel"
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.45 }}
                >
                    <div className="chart-panel-header">
                        <div>
                            <h4>Hiring Funnel</h4>
                            <p>Candidate pipeline conversion rates</p>
                        </div>
                    </div>
                    <div className="funnel-container">
                        {hiringFunnel.map((stage, i) => (
                            <motion.div
                                key={stage.stage}
                                className="funnel-stage-row"
                                initial={{ opacity: 0, x: -20 }}
                                animate={{ opacity: 1, x: 0 }}
                                transition={{ delay: 0.5 + i * 0.08 }}
                            >
                                <span className="funnel-label">{stage.stage}</span>
                                <div className="funnel-bar-wrap">
                                    <motion.div
                                        className="funnel-bar-fill"
                                        style={{ background: FUNNEL_COLORS[i] }}
                                        initial={{ width: 0 }}
                                        animate={{ width: `${stage.percentage}%` }}
                                        transition={{ delay: 0.6 + i * 0.08, duration: 0.6 }}
                                    >
                                        {stage.percentage >= 15 ? stage.label : ""}
                                    </motion.div>
                                </div>
                                <span className="funnel-count">{stage.count}</span>
                            </motion.div>
                        ))}
                    </div>
                </motion.div>

                {/* Monthly Comparison Bar Chart */}
                <motion.div
                    className="analytics-chart-panel"
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.5 }}
                >
                    <div className="chart-panel-header">
                        <div>
                            <h4>Year-over-Year Comparison</h4>
                            <p>Applications volume: 2025 vs 2026</p>
                        </div>
                        <div className="comparison-legend">
                            <div className="legend-item">
                                <div className="legend-dot" style={{ background: "#6366F1" }} />
                                2025
                            </div>
                            <div className="legend-item">
                                <div className="legend-dot" style={{ background: "#3B82F6" }} />
                                2026
                            </div>
                        </div>
                    </div>
                    <div className="chart-area">
                        <Bar data={comparisonData} options={barChartOptions} />
                    </div>
                </motion.div>
            </div>

            {/* Department Breakdown */}
            <motion.div
                className="analytics-chart-panel"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.55 }}
            >
                <div className="chart-panel-header">
                    <div>
                        <h4>Department Hiring Breakdown</h4>
                        <p>Open roles, applicant volume, hires, and budget per department</p>
                    </div>
                </div>
                <table className="dept-table">
                    <thead>
                        <tr>
                            <th>Department</th>
                            <th style={{ textAlign: "center" }}>Open Jobs</th>
                            <th style={{ textAlign: "center" }}>Applicants</th>
                            <th style={{ textAlign: "center" }}>Hires</th>
                            <th style={{ textAlign: "center" }}>Budget</th>
                        </tr>
                    </thead>
                    <tbody>
                        {departmentData.map((dept, i) => (
                            <motion.tr
                                key={dept.department}
                                initial={{ opacity: 0 }}
                                animate={{ opacity: 1 }}
                                transition={{ delay: 0.6 + i * 0.06 }}
                            >
                                <td style={{ fontWeight: 600 }}>{dept.department}</td>
                                <td>{dept.openJobs}</td>
                                <td>{dept.applicants}</td>
                                <td style={{ color: "var(--success)", fontWeight: 600 }}>{dept.hires}</td>
                                <td>{dept.budget}</td>
                            </motion.tr>
                        ))}
                    </tbody>
                </table>
            </motion.div>

            {/* Recruiter Performance */}
            <motion.div
                className="analytics-chart-panel"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.6 }}
            >
                <div className="chart-panel-header">
                    <div>
                        <h4>Recruiter Performance Scorecard</h4>
                        <p>Individual recruiter metrics and offer acceptance rates</p>
                    </div>
                </div>
                <table className="recruiter-table">
                    <thead>
                        <tr>
                            <th>Recruiter</th>
                            <th style={{ textAlign: "center" }}>Active Campaigns</th>
                            <th style={{ textAlign: "center" }}>Avg. Time to Hire</th>
                            <th style={{ textAlign: "center" }}>Selections</th>
                            <th style={{ textAlign: "center" }}>Offer Acceptance</th>
                        </tr>
                    </thead>
                    <tbody>
                        {recruiterData.map((rec, i) => (
                            <motion.tr
                                key={rec.name}
                                initial={{ opacity: 0 }}
                                animate={{ opacity: 1 }}
                                transition={{ delay: 0.65 + i * 0.06 }}
                            >
                                <td>
                                    <div className="rec-name-cell">
                                        <div className="rec-avatar-sm">
                                            {rec.name.split(" ").map(n => n[0]).join("").slice(0, 2)}
                                        </div>
                                        {rec.name}
                                    </div>
                                </td>
                                <td>{rec.activeCampaigns}</td>
                                <td>{rec.averageTimeToHire}</td>
                                <td style={{ color: "var(--success)", fontWeight: 600 }}>{rec.selections}</td>
                                <td>
                                    <div className="oar-bar">
                                        <div className="oar-track">
                                            <div className="oar-fill" style={{ width: `${rec.offerAcceptanceRate}%` }} />
                                        </div>
                                        <span style={{ fontSize: "12px", fontWeight: 600 }}>{rec.offerAcceptanceRate}%</span>
                                    </div>
                                </td>
                            </motion.tr>
                        ))}
                    </tbody>
                </table>
            </motion.div>
        </div>
    );
}