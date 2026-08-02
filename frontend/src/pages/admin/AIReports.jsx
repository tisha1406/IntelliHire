import { useState, useEffect } from "react";
import { Download, FileText, BarChart3 } from "lucide-react";
import DashboardGrid from "../../layouts/DashboardGrid";
import PageHeader from "../../components/layout/PageHeader";
import SectionCard from "../../components/layout/SectionCard";
import StatGrid from "../../components/layout/StatGrid";
import Card from "../../components/common/Card";
import Button from "../../components/common/Button";
import Badge from "../../components/common/Badge";
import DataTable from "../../components/common/DataTable";
import DonutChart from "../../components/charts/DonutChart";
import HorizontalBarChart from "../../components/charts/HorizontalBarChart";
import { AIReportsAPI } from "../../api/ai_reports";

const reportTypes = [
    {
        id: "executive",
        title: "Executive Summary",
        description: "High-level platform KPIs, hiring funnel, and AI model performance.",
        icon: BarChart3,
        badge: "Popular",
        color: "#2563EB",
    },
    {
        id: "company",
        title: "Company Performance Report",
        description: "Per-company breakdown of interviews, candidates, and completion rates.",
        icon: FileText,
        badge: null,
        color: "#8B5CF6",
    },
    {
        id: "candidate",
        title: "Candidate Analytics Report",
        description: "Readiness scores, risk distribution, and pass/fail analysis.",
        icon: FileText,
        badge: null,
        color: "#22c55e",
    },
    {
        id: "ai_usage",
        title: "AI Usage & Cost Report",
        description: "Token consumption, model usage, and cost breakdown by company.",
        icon: FileText,
        badge: "New",
        color: "#f59e0b",
    },
];



export default function AIReports() {
    const [selected, setSelected] = useState("executive");
    const [dateRange, setDateRange] = useState("month");
    const [reports, setReports] = useState([]);
    const [execSummary, setExecSummary] = useState(null);
    const [scores, setScores] = useState([]);
    const [completionRates, setCompletionRates] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchDashboard = async () => {
            try {
                const s = await AIReportsAPI.getScoreDistribution(dateRange);
                const c = await AIReportsAPI.getCompanyCompletion(dateRange);
                const e = await AIReportsAPI.getReport("executive", dateRange);
                setScores(s);
                setCompletionRates(c);
                setExecSummary(e);
            } catch (err) {
                console.error(err);
            }
        };
        fetchDashboard();
    }, [dateRange]);

    useEffect(() => {
        const fetchReports = async () => {
            setLoading(true);
            try {
                const data = await AIReportsAPI.getReport(selected, dateRange);
                
                // Format data for the table based on selected type
                if (selected === "executive") {
                    const formatted = [
                        { metric: "Companies", value: data.companies },
                        { metric: "Recruiters", value: data.recruiters },
                        { metric: "Candidates", value: data.candidates },
                        { metric: "Completed Interviews", value: data.completed_interviews },
                        { metric: "Overall AI Accuracy", value: `${data.overall_ai_accuracy}%` }
                    ];
                    setReports(formatted);
                } else if (selected === "company" || selected === "candidate" || selected === "usage" || selected === "ai_usage") {
                    setReports(Array.isArray(data) ? data : (data.records || data || []));
                }
            } catch (err) {
                console.error(err);
                setReports([]);
            } finally {
                setLoading(false);
            }
        };
        fetchReports();
    }, [selected, dateRange]);

    const getColumns = () => {
        if (selected === "executive") return [
            { title: "Metric", dataIndex: "metric" },
            { title: "Value", dataIndex: "value", align: "right" }
        ];
        if (selected === "company") return [
            { title: "Company", dataIndex: "company" },
            { title: "Interviews", dataIndex: "interview_count", align: "right" },
            { title: "Completion %", dataIndex: "completion_percentage", align: "right", render: v => `${v}%` },
            { title: "Candidates", dataIndex: "candidates", align: "right" },
        ];
        if (selected === "candidate") return [
            { title: "Candidate", dataIndex: "candidate" },
            { title: "Resume Score", dataIndex: "resume_score", align: "right" },
            { title: "Tech Score", dataIndex: "technical_score", align: "right" },
            { title: "Behavior Score", dataIndex: "behaviour_score", align: "right" },
        ];
        if (selected === "ai_usage") return [
            { title: "Provider", dataIndex: "llm_provider" },
            { title: "Requests", dataIndex: "requests", align: "right" },
            { title: "Tokens", dataIndex: "tokens_used", align: "right" },
            { title: "Cost", dataIndex: "estimated_cost", align: "right", render: v => `$${v}` },
        ];
        return [];
    };

    return (
        <DashboardGrid>
            <PageHeader
                title="AI Reports"
                description="Generate and export AI-powered analytics reports for the platform."
                rightContent={
                    <div style={{ display: 'flex', gap: '10px' }}>
                        <select
                            value={dateRange}
                            onChange={e => setDateRange(e.target.value)}
                            style={{ padding: '8px 14px', borderRadius: '8px', border: '1px solid var(--border)', background: 'var(--card)', color: 'var(--text)', fontSize: '14px', cursor: 'pointer' }}
                        >
                            <option value="week">Last 7 Days</option>
                            <option value="month">Last 30 Days</option>
                            <option value="quarter">Last Quarter</option>
                            <option value="year">This Year</option>
                        </select>
                        <Button variant="outline"><Download size={16} /> Export PDF</Button>
                        <Button variant="primary"><Download size={16} /> Export CSV</Button>
                    </div>
                }
            />

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '16px' }}>
                {reportTypes.map(r => {
                    const Icon = r.icon;
                    const isSelected = selected === r.id;
                    return (
                        <div
                            key={r.id}
                            onClick={() => setSelected(r.id)}
                            style={{
                                padding: '20px', borderRadius: '12px', cursor: 'pointer',
                                border: `2px solid ${isSelected ? r.color : 'var(--border)'}`,
                                background: isSelected ? `${r.color}10` : 'var(--card)',
                                transition: 'all 0.2s ease',
                            }}
                        >
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '12px' }}>
                                <div style={{ width: '40px', height: '40px', borderRadius: '10px', background: `${r.color}20`, display: 'flex', alignItems: 'center', justifyContent: 'center', color: r.color }}>
                                    <Icon size={20} />
                                </div>
                                {r.badge && <Badge variant={r.badge === 'New' ? 'success' : 'primary'}>{r.badge}</Badge>}
                            </div>
                            <div style={{ fontWeight: '600', color: 'var(--text)', marginBottom: '4px' }}>{r.title}</div>
                            <div style={{ fontSize: '13px', color: 'var(--text-secondary)', lineHeight: '1.5' }}>{r.description}</div>
                        </div>
                    );
                })}
            </div>

            <StatGrid>
                {[
                    { label: "Total Interviews (Period)", value: execSummary ? (execSummary.completed_interviews || 0) : 0 },
                    { label: "Completion Rate", value: "94.2%" },
                    { label: "Avg Score", value: "78%" },
                    { label: "Companies Active", value: execSummary ? (execSummary.companies || 0) : 0 },
                ].map(({ label, value }) => (
                    <Card key={label} className="ih-card">
                        <div style={{ color: 'var(--text-secondary)', fontSize: '13px', marginBottom: '8px' }}>{label}</div>
                        <div style={{ fontSize: '28px', fontWeight: 'bold', color: 'var(--text)' }}>{value}</div>
                    </Card>
                ))}
            </StatGrid>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
                <SectionCard>
                    <h3 style={{ fontSize: '15px', fontWeight: '600', color: 'var(--text)', padding: '20px 24px 0', marginBottom: '4px' }}>Score Distribution</h3>
                    <div style={{ padding: '0 24px 24px' }}>
                        {scores.length === 0 || scores.every(s => s.value === 0) ? (
                            <div style={{ height: 260, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)' }}>No interview data available.</div>
                        ) : (
                            <DonutChart data={scores} height={260} />
                        )}
                    </div>
                </SectionCard>
                <SectionCard>
                    <h3 style={{ fontSize: '15px', fontWeight: '600', color: 'var(--text)', padding: '20px 24px 0', marginBottom: '4px' }}>Company Completion Rate</h3>
                    <div style={{ padding: '0 24px 24px' }}>
                        {completionRates.length === 0 ? (
                            <div style={{ height: 260, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)' }}>No AI analytics yet.</div>
                        ) : (
                            <HorizontalBarChart data={completionRates} nameKey="name" valueKey="value" height={260} />
                        )}
                    </div>
                </SectionCard>
            </div>

            <SectionCard>
                <h3 style={{ fontSize: '15px', fontWeight: '600', color: 'var(--text)', padding: '20px 24px 16px' }}>Report Data</h3>
                <div style={{ padding: '0 0 8px' }}>
                    {loading ? <div style={{ padding: '24px', textAlign: 'center' }}>Loading...</div> : (
                        reports.length === 0 ? <div style={{ padding: '24px', textAlign: 'center', color: 'var(--text-muted)' }}>No reports available.</div> : <DataTable columns={getColumns()} data={reports} keyField={selected === "executive" ? "metric" : (selected === "ai_usage" ? "llm_provider" : "id")} searchable={true} />
                    )}
                </div>
            </SectionCard>
        </DashboardGrid>
    );
}
