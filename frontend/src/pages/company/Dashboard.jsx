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
    FaBriefcase,
    FaUsers,
    FaRobot,
    FaChartLine,
    FaTasks,
    FaBullhorn,
    FaArrowRight,
    FaPlus,
    FaShieldAlt
} from "react-icons/fa";
import { Link, useNavigate } from "react-router-dom";
import { useAuthContext } from "../../context/AuthContext";
import { usePermissions } from "../../context/PermissionsContext";

import PageHeader from "../../components/common/PageHeader";
import StatsCard from "../../components/common/StatsCard";
import Card from "../../components/common/Card";
import Button from "../../components/common/Button";
import StatusBadge from "../../components/common/StatusBadge";
import Badge from "../../components/common/Badge";
import dashboardService from "../../services/company/dashboardService";

// Personal task list is local-only (no backend yet)
// We will replace this with Platform Overview
// import { mockTodayTasks } from "../../mock/dashboard";

import "../../styles/company/Dashboard.css";

ChartJS.register(
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    BarElement,
    ArcElement,
    Tooltip,
    Legend,
    Filler
);

const containerVariants = {
    hidden: { opacity: 0 },
    show: { opacity: 1, transition: { staggerChildren: 0.08 } }
};

const itemVariants = {
    hidden: { opacity: 0, y: 15 },
    show: { opacity: 1, y: 0, transition: { type: "spring", stiffness: 300, damping: 25 } }
};

const iconMap = {
    campaign: <FaBriefcase />,
    users: <FaUsers />,
    robot: <FaRobot />,
    chart: <FaChartLine />,
};

const colorMap = {
    campaign: "linear-gradient(135deg, #3B82F6, #60A5FA)",
    users: "linear-gradient(135deg, #8B5CF6, #C084FC)",
    robot: "linear-gradient(135deg, #10B981, #34D399)",
    chart: "linear-gradient(135deg, #F59E0B, #FBBF24)",
};

export default function Dashboard() {
    const navigate = useNavigate();
    const { companyProfile } = useAuthContext();
    const { subscription, limits, features, platform } = usePermissions();

    // Live data state from /company/dashboard
    const [dashboardData, setDashboardData] = useState(null);
    const [stats, setStats] = useState(null);
    const [recentCandidates, setRecentCandidates] = useState([]);
    const [recentInterviews, setRecentInterviews] = useState([]);
    const [recentNotifications, setRecentNotifications] = useState([]);
    const [hiringTrend, setHiringTrend] = useState([]);
    const [hiringFunnel, setHiringFunnel] = useState([]);
    const [recruiterPerf, setRecruiterPerf] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const loadDashboard = async () => {
            setLoading(true);
            try {
                const res = await dashboardService.getDashboard();
                const data = res.data?.data || res.data || {};

                setDashboardData(data);
                setStats(data.kpis || null);
                setRecentCandidates(data.recent_candidates || []);
                setRecentInterviews(data.recent_interviews || []);
                setRecentNotifications(data.recent_notifications || []);
                setHiringTrend(data.hiring_trend || []);
                setHiringFunnel(data.hiring_funnel || []);

                // Recruiter performance comes from analytics endpoint separately
                try {
                    const recRes = await dashboardService.getRecruiterPerformance();
                    setRecruiterPerf(recRes.data?.data || recRes.data || []);
                } catch { /* no recruiter data yet */ }

            } catch (err) {
                console.error("Dashboard load error:", err);
            } finally {
                setLoading(false);
            }
        };
        loadDashboard();
    }, []);




    // Build live stat cards from backend KPIs
    const kpis = stats || {};
    const statCards = stats
        ? [
            {
                id: "stat-1", title: "Total Applications",
                value: kpis.totalApplications?.value || "0",
                change: "",
                icon: "campaign", positive: true,
            },
            {
                id: "stat-2", title: "Total Interviews",
                value: kpis.totalInterviews?.value || "0",
                change: "",
                icon: "robot", positive: true,
            },
            {
                id: "stat-3", title: "Active Campaigns",
                value: dashboardData?.usage?.active_campaigns ?? "0",
                change: "",
                icon: "users", positive: true,
            },
            {
                id: "stat-4", title: "Candidates Hired",
                value: dashboardData?.usage?.hired_candidates ?? "0",
                change: "",
                icon: "chart", positive: true,
            },
        ]
        : [];

    // ─── Chart: Applications Trend (Line) ─────────────────────────────────────
    const lineData = {
        labels: hiringTrend.length > 0 ? hiringTrend.map(d => d.month) : ["Jan","Feb","Mar","Apr","May","Jun"],
        datasets: [
            {
                label: "Applications",
                data: hiringTrend.length > 0 ? hiringTrend.map(d => d.applications) : [0,0,0,0,0,0],
                borderColor: "#3B82F6",
                backgroundColor: "rgba(59, 130, 246, 0.12)",
                fill: true,
                tension: 0.4,
                pointRadius: 4,
            },
        ],
    };

    // ─── Chart: Hiring Funnel (Bar) ─────────────────────────────────────────────
    const barData = {
        labels: hiringFunnel.length > 0 ? hiringFunnel.map(d => d.stage) : ["Applied","AI Screened","Interview","Offered","Hired"],
        datasets: [
            {
                label: "Candidates",
                data: hiringFunnel.length > 0 ? hiringFunnel.map(d => d.count) : [0,0,0,0,0],
                backgroundColor: [
                    "rgba(59, 130, 246, 0.8)",
                    "rgba(96, 165, 250, 0.8)",
                    "rgba(139, 92, 246, 0.8)",
                    "rgba(16, 185, 129, 0.8)",
                    "rgba(245, 158, 11, 0.8)",
                ],
                borderWidth: 0,
                borderRadius: 8,
            },
        ],
    };

    // ─── Chart: Department Hiring (Doughnut) — use hiring funnel if no dept data ──
    const doughnutLabels = hiringFunnel.length > 0 ? hiringFunnel.map(d => d.stage) : ["No Data"];
    const doughnutValues = hiringFunnel.length > 0 ? hiringFunnel.map(d => d.count) : [1];
    const doughnutData = {
        labels: doughnutLabels,
        datasets: [
            {
                data: doughnutValues,
                backgroundColor: ["#3B82F6", "#8B5CF6", "#C084FC", "#10B981", "#F59E0B"],
                borderWidth: 0,
            },
        ],
    };

    return (
        <motion.div
            className="dashboard-page-container"
            variants={containerVariants}
            initial="hidden"
            animate="show"
        >
            <PageHeader
                title={`${companyProfile?.company_name || "Company"} Dashboard`}
                subtitle="Recruitment overview"
                breadcrumbs={[]}
                actions={
                    <div className="header-dashboard-cta">
                        <Button
                            variant="primary"
                            size="sm"
                            iconLeft={<FaPlus />}
                            onClick={() => navigate("/company/campaigns/new")}
                        >
                            New Campaign
                        </Button>
                    </div>
                }
            />

            {/* Statistics Cards */}
            <motion.div className="dashboard-stats-grid" variants={itemVariants}>
                {statCards.map((stat) => (
                    <StatsCard
                        key={stat.id}
                        title={stat.title}
                        value={stat.value}
                        change={stat.change}
                        icon={iconMap[stat.icon]}
                        color={colorMap[stat.icon]}
                        isPositive={stat.positive}
                    />
                ))}
            </motion.div>

            {/* Charts section */}
            <motion.div className="dashboard-charts-layout" variants={itemVariants}>
                <Card className="chart-card-holder line-chart-span">
                    <div className="chart-title-area">
                        <h4>Applications Trend</h4>
                        <span>Monthly applications</span>
                    </div>
                    <div className="chart-embed">
                        <Line
                            data={lineData}
                            options={{
                                responsive: true,
                                maintainAspectRatio: false,
                                plugins: { legend: { display: false } }
                            }}
                        />
                    </div>
                </Card>

                <Card className="chart-card-holder">
                    <div className="chart-title-area">
                        <h4>Hiring Funnel Conversion</h4>
                        <span>Candidate pipeline</span>
                    </div>
                    <div className="chart-embed">
                        <Bar
                            data={barData}
                            options={{
                                responsive: true,
                                maintainAspectRatio: false,
                                plugins: { legend: { display: false } }
                            }}
                        />
                    </div>
                </Card>

                <Card className="chart-card-holder">
                    <div className="chart-title-area">
                        <h4>Hires by Department</h4>
                        <span>Department wise</span>
                    </div>
                    <div className="chart-embed">
                        <Doughnut
                            data={doughnutData}
                            options={{
                                responsive: true,
                                maintainAspectRatio: false,
                                cutout: "70%",
                                plugins: { legend: { position: "bottom", labels: { boxWidth: 10 } } }
                            }}
                        />
                    </div>
                </Card>
            </motion.div>

            {/* Widgets */}
            <motion.div className="dashboard-widgets-grid" variants={itemVariants}>
                {/* Platform Overview */}
                <Card className="widget-panel">
                    <div className="widget-header">
                        <h4><FaShieldAlt className="widget-icon" /> Platform Overview</h4>
                    </div>
                    <div className="widget-list">
                        <div style={{ padding: "12px", borderBottom: "1px solid var(--border)", display: 'flex', justifyContent: 'space-between' }}>
                            <div>
                                <h5 style={{ margin: "0 0 4px 0" }}>Plan: {subscription?.plan_id?.toUpperCase() || "TRIAL"}</h5>
                                <Badge variant={subscription?.status === "active" ? "success" : "warning"}>
                                    {subscription?.status || "active"}
                                </Badge>
                            </div>
                            <div style={{ textAlign: 'right' }}>
                                <span style={{ fontSize: "12px", color: "var(--text-secondary)", display: 'block' }}>Features</span>
                                <strong>{Object.keys(features || {}).filter(k => features[k]).length} Active</strong>
                            </div>
                        </div>
                        <div style={{ padding: "12px", borderBottom: "1px solid var(--border)" }}>
                            <h5 style={{ margin: "0 0 4px 0" }}>Allowed Capabilities</h5>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', fontSize: "12px", color: "var(--text-secondary)" }}>
                                <div><strong>AI Models:</strong> {(platform?.allowed_ai_models || []).join(", ") || "Default"}</div>
                                <div><strong>Languages:</strong> {(platform?.allowed_languages || []).join(", ") || "Default"}</div>
                                <div><strong>Voice Models:</strong> {(platform?.allowed_voices || []).join(", ") || "Default"}</div>
                            </div>
                        </div>
                        <div style={{ padding: "12px" }}>
                            <h5 style={{ margin: "0 0 8px 0" }}>Usage vs Limits</h5>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', fontSize: "12px", color: "var(--text-secondary)" }}>
                                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                                    <span>Recruiters</span>
                                    <span>{dashboardData?.usage?.recruiters_used ?? 0} / {limits?.max_recruiters ?? "∞"}</span>
                                </div>
                                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                                    <span>Campaigns</span>
                                    <span>{dashboardData?.usage?.campaigns_used ?? 0} / {limits?.max_campaigns ?? "∞"}</span>
                                </div>
                                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                                    <span>Candidates</span>
                                    <span>{dashboardData?.usage?.candidates_used ?? 0} / {limits?.max_candidates ?? "∞"}</span>
                                </div>
                                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                                    <span>Storage Used</span>
                                    <span>{dashboardData?.usage?.storage_used_gb ?? "0"}GB / {limits?.storage_limit_gb ?? "∞"}GB</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </Card>

                {/* Hiring Goals from funnel data */}
                <Card className="widget-panel">
                    <div className="widget-header">
                        <h4>Hiring Funnel</h4>
                    </div>
                    <div className="widget-list objectives-scroll">
                        {hiringFunnel.length > 0
                            ? hiringFunnel.map((stage, index) => (
                                <div key={index} className="hiring-objective-row">
                                    <div className="hiring-obj-meta">
                                        <span className="hiring-obj-dept">{stage.stage}</span>
                                        <span className="hiring-obj-count">{stage.count}</span>
                                    </div>
                                    <div className="hiring-obj-bar-bg">
                                        <div
                                            className="hiring-obj-bar-fill"
                                            style={{
                                                width: `${Math.min(stage.percentage, 100)}%`,
                                                background: index % 2 === 0 ? "var(--primary)" : "var(--success)",
                                            }}
                                        />
                                    </div>
                                </div>
                            ))
                            : (
                                <div style={{ color: "var(--text-secondary)", fontSize: 13, padding: "12px 0" }}>
                                    No funnel data available.
                                </div>
                            )
                        }
                    </div>
                </Card>

                {/* Recruiter Leaderboard */}
                <Card className="widget-panel">
                    <div className="widget-header">
                        <h4>Leaderboard</h4>
                    </div>
                    <div className="widget-list leaderboard-scroll">
                        {recruiterPerf.slice(0, 4).map((rec, index) => (
                            <div key={index} className="leaderboard-item">
                                <div className="leaderboard-rec-avatar">
                                    {rec.name.split(" ").map(x => x[0]).join("")}
                                </div>
                                <div className="leaderboard-meta">
                                    <h5>{rec.name}</h5>
                                </div>
                                <div className="leaderboard-metrics-col">
                                    <strong>{rec.selections}</strong>
                                </div>
                            </div>
                        ))}
                    </div>
                </Card>
            </motion.div>

            {/* Bottom: Announcements + Interviews + Candidates */}
            <motion.div className="dashboard-bottom-flex" variants={itemVariants}>
                {/* Notifications / Announcements (live from backend) */}
                <Card className="widget-panel">
                    <div className="widget-header">
                        <h4><FaBullhorn className="widget-icon" /> Notifications</h4>
                    </div>
                    <div className="widget-list announcements-scroll">
                        {recentNotifications.length > 0
                            ? recentNotifications.map((ann) => (
                                <div key={ann.id} className="announcement-item-box">
                                    <div className="ann-title-line">
                                        <h5>{ann.title}</h5>
                                        <span>{ann.created_at ? new Date(ann.created_at).toLocaleDateString() : ""}</span>
                                    </div>
                                    <p style={{ fontSize: 12, color: "var(--text-secondary)", marginTop: 4 }}>
                                        {ann.message}
                                    </p>
                                </div>
                            ))
                            : (
                                <div style={{ color: "var(--text-secondary)", fontSize: 13, padding: "12px 0" }}>
                                    No notifications yet.
                                </div>
                            )
                        }
                    </div>
                </Card>

                {/* Recent AI Interviews (live) */}
                <Card className="bottom-panel-item">
                    <div className="panel-header-row">
                        <h4>Recent AI Interviews</h4>
                        <Link to="/company/interviews" className="view-all-link">
                            View All <FaArrowRight />
                        </Link>
                    </div>
                    <div className="panel-list-view">
                        {recentInterviews.length > 0
                            ? recentInterviews.map((interview) => (
                                <div key={interview.id} className="simple-interview-row">
                                    <div className="interview-datetime">
                                        <strong>{interview.overall_score != null ? `${interview.overall_score}%` : "—"}</strong>
                                        <span>Score</span>
                                    </div>
                                    <div className="interview-details">
                                        <h5>{interview.candidate_id || "Candidate"}</h5>
                                        <p>{interview.status || "—"}</p>
                                    </div>
                                    <StatusBadge status={interview.status || "Pending"} />
                                </div>
                            ))
                            : (
                                <div style={{ color: "var(--text-secondary)", fontSize: 13, padding: "12px 0" }}>
                                    No interviews found.
                                </div>
                            )
                        }
                    </div>
                </Card>

                {/* Recent Candidates (live) */}
                <Card className="bottom-panel-item">
                    <div className="panel-header-row">
                        <h4>Recent Candidates</h4>
                        <Link to="/company/candidates" className="view-all-link">
                            Candidate ATS <FaArrowRight />
                        </Link>
                    </div>
                    <div className="panel-list-view">
                        {recentCandidates.length > 0
                            ? recentCandidates.map((cand) => {
                                const name = cand.name || cand.full_name || "Candidate";
                                const score = cand.aiMatch ?? cand.match_score ?? cand.ai_score ?? null;
                                return (
                                    <div key={cand.id || cand._id} className="simple-cand-row">
                                        <div className="cand-avatar-initials">
                                            {name.split(" ").map(x => x[0]).join("")}
                                        </div>
                                        <div className="cand-name-meta">
                                            <h5>{name}</h5>
                                        </div>
                                        {score !== null && (
                                            <div className="cand-match-val">
                                                <span className="match-label">Match</span>
                                                <span className="match-percent">{score}%</span>
                                            </div>
                                        )}
                                    </div>
                                );
                            })
                            : (
                                <div style={{ color: "var(--text-secondary)", fontSize: 13, padding: "12px 0" }}>
                                    No recent candidates found.
                                </div>
                            )
                        }
                    </div>
                </Card>
            </motion.div>
        </motion.div>
    );
}