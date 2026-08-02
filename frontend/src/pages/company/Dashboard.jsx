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
} from "react-icons/fa";
import { Link, useNavigate } from "react-router-dom";

import PageHeader from "../../components/common/PageHeader";
import StatsCard from "../../components/common/StatsCard";
import Card from "../../components/common/Card";
import Button from "../../components/common/Button";
import StatusBadge from "../../components/common/StatusBadge";
import Badge from "../../components/common/Badge";
import dashboardService from "../../services/company/dashboardService";

// Static data: tasks + announcements (no backend for these)
import {
    mockTodayTasks,
    mockAnnouncements,
    mockHiringProgress,
} from "../../mock/dashboard";

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
    const [tasks, setTasks] = useState(mockTodayTasks);

    // Live data state
    const [stats, setStats] = useState(null);
    const [recentCandidates, setRecentCandidates] = useState([]);
    const [upcomingInterviews, setUpcomingInterviews] = useState([]);
    const [hiringTrend, setHiringTrend] = useState([]);
    const [hiringFunnel, setHiringFunnel] = useState([]);
    const [deptBreakdown, setDeptBreakdown] = useState([]);
    const [recruiterPerf, setRecruiterPerf] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const loadDashboard = async () => {
            setLoading(true);
            try {
                const [
                    kpisRes,
                    candidatesRes,
                    interviewsRes,
                    trendRes,
                    funnelRes,
                    deptRes,
                    recRes,
                ] = await Promise.allSettled([
                    dashboardService.getStats(),
                    dashboardService.getRecentCandidates(),
                    dashboardService.getUpcomingInterviews(),
                    dashboardService.getHiringTrend(),
                    dashboardService.getHiringFunnel(),
                    dashboardService.getDepartmentBreakdown(),
                    dashboardService.getRecruiterPerformance(),
                ]);

                if (kpisRes.status === "fulfilled") setStats(kpisRes.value.data);
                if (candidatesRes.status === "fulfilled") {
                    const data = candidatesRes.value.data;
                    setRecentCandidates(Array.isArray(data) ? data.slice(0, 4) : (data?.candidates || []).slice(0, 4));
                }
                if (interviewsRes.status === "fulfilled") {
                    const data = interviewsRes.value.data;
                    setUpcomingInterviews(Array.isArray(data) ? data.slice(0, 4) : []);
                }
                if (trendRes.status === "fulfilled") setHiringTrend(trendRes.value.data || []);
                if (funnelRes.status === "fulfilled") setHiringFunnel(funnelRes.value.data || []);
                if (deptRes.status === "fulfilled") setDeptBreakdown(deptRes.value.data || []);
                if (recRes.status === "fulfilled") setRecruiterPerf(recRes.value.data || []);
            } catch (err) {
                console.error("Dashboard load error:", err);
            } finally {
                setLoading(false);
            }
        };
        loadDashboard();
    }, []);

    const handleToggleTask = (taskId) => {
        setTasks(tasks.map((t) => (t.id === taskId ? { ...t, done: !t.done } : t)));
    };

    // Build live stat cards from backend KPIs
    const statCards = stats
        ? [
            {
                id: "stat-1", title: "Total Applications",
                value: stats.totalApplications?.value || "—",
                change: stats.totalApplications?.change || "",
                icon: "campaign", positive: true
            },
            {
                id: "stat-2", title: "Total Candidates",
                value: stats.totalApplications?.value || "—",
                change: stats.totalApplications?.change || "",
                icon: "users", positive: true
            },
            {
                id: "stat-3", title: "Interviews Conducted",
                value: stats.totalInterviews?.value || "—",
                change: stats.totalInterviews?.change || "",
                icon: "robot", positive: true
            },
            {
                id: "stat-4", title: "Offer Acceptance Rate",
                value: stats.offerAcceptanceRate?.value || "—",
                change: stats.offerAcceptanceRate?.change || "",
                icon: "chart", positive: true
            },
        ]
        : [];

    // ─── Chart: Applications Trend (Line) ─────────────────────────────────────
    const lineData = {
        labels: hiringTrend.length > 0 ? hiringTrend.map(d => d.month) : ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul"],
        datasets: [
            {
                label: "Applications",
                data: hiringTrend.length > 0 ? hiringTrend.map(d => d.applications) : [45, 72, 61, 98, 121, 140, 185],
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
        labels: hiringFunnel.length > 0 ? hiringFunnel.map(d => d.stage) : ["Applied", "AI Screened", "Assessments", "Interviews", "Hired"],
        datasets: [
            {
                label: "Candidates",
                data: hiringFunnel.length > 0 ? hiringFunnel.map(d => d.count) : [850, 510, 306, 122, 38],
                backgroundColor: [
                    "rgba(59, 130, 246, 0.8)",
                    "rgba(96, 165, 250, 0.8)",
                    "rgba(139, 92, 246, 0.8)",
                    "rgba(16, 185, 129, 0.8)",
                    "rgba(245, 158, 11, 0.8)",
                    "rgba(236, 72, 153, 0.8)",
                ],
                borderWidth: 0,
                borderRadius: 8,
            },
        ],
    };

    // ─── Chart: Department Hiring (Doughnut) ────────────────────────────────────
    const doughnutData = {
        labels: deptBreakdown.length > 0 ? deptBreakdown.map(d => d.department) : ["Engineering", "AI & Data Science", "Product/Design", "Sales/Marketing", "HR"],
        datasets: [
            {
                data: deptBreakdown.length > 0 ? deptBreakdown.map(d => d.hires) : [18, 8, 5, 6, 1],
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
                title="Dashboard"
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
                {/* Tasks */}
                <Card className="widget-panel">
                    <div className="widget-header">
                        <h4><FaTasks className="widget-icon" /> Tasks</h4>
                    </div>
                    <div className="widget-list tasks-scrollable">
                        {tasks.map((task) => (
                            <label key={task.id} className={`task-item-row ${task.done ? "is-done" : ""}`}>
                                <input
                                    type="checkbox"
                                    checked={task.done}
                                    onChange={() => handleToggleTask(task.id)}
                                    className="task-checkbox"
                                />
                                <span className="task-text-content">
                                    {task.task.length > 28 ? task.task.substring(0, 28) + "..." : task.task}
                                </span>
                                <Badge
                                    variant={task.priority === "High" ? "danger" : task.priority === "Medium" ? "warning" : "neutral"}
                                    className="task-priority-badge"
                                >
                                    {task.priority}
                                </Badge>
                            </label>
                        ))}
                    </div>
                </Card>

                {/* Hiring Goals */}
                <Card className="widget-panel">
                    <div className="widget-header">
                        <h4>Hiring Goals</h4>
                    </div>
                    <div className="widget-list objectives-scroll">
                        {mockHiringProgress.map((obj, index) => (
                            <div key={index} className="hiring-objective-row">
                                <div className="hiring-obj-meta">
                                    <span className="hiring-obj-dept">{obj.department}</span>
                                    <span className="hiring-obj-count">{obj.currentHires} / {obj.targetHires}</span>
                                </div>
                                <div className="hiring-obj-bar-bg">
                                    <div
                                        className="hiring-obj-bar-fill"
                                        style={{
                                            width: `${obj.progress}%`,
                                            background: index % 2 === 0 ? "var(--primary)" : "var(--success)"
                                        }}
                                    />
                                </div>
                            </div>
                        ))}
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
                {/* Announcements (static) */}
                <Card className="widget-panel">
                    <div className="widget-header">
                        <h4><FaBullhorn className="widget-icon" /> Announcements</h4>
                    </div>
                    <div className="widget-list announcements-scroll">
                        {mockAnnouncements.map((ann) => (
                            <div key={ann.id} className="announcement-item-box">
                                <div className="ann-title-line">
                                    <h5>{ann.title}</h5>
                                    <span>{ann.date}</span>
                                </div>
                            </div>
                        ))}
                    </div>
                </Card>

                {/* Upcoming AI Interviews (live) */}
                <Card className="bottom-panel-item">
                    <div className="panel-header-row">
                        <h4>Upcoming AI Interviews</h4>
                        <Link to="/company/interviews" className="view-all-link">
                            Schedule Portal <FaArrowRight />
                        </Link>
                    </div>
                    <div className="panel-list-view">
                        {upcomingInterviews.length > 0
                            ? upcomingInterviews.map((int) => (
                                <div key={int.id || int._id} className="simple-interview-row">
                                    <div className="interview-datetime">
                                        <strong>{int.time || int.scheduled_time || "—"}</strong>
                                        <span>{int.date || int.scheduled_date || "—"}</span>
                                    </div>
                                    <div className="interview-details">
                                        <h5>{int.candidate || int.candidate_name || int.name || "Candidate"}</h5>
                                        <p>{int.position || int.role || "Position"}</p>
                                    </div>
                                    <StatusBadge status={int.status || "Scheduled"} />
                                </div>
                            ))
                            : (
                                <div style={{ color: "var(--text-secondary)", fontSize: 13, padding: "12px 0" }}>
                                    No upcoming interviews found.
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