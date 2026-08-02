import { useState, useEffect } from "react";
import { Download } from "lucide-react";
import DashboardGrid from "../../layouts/DashboardGrid";
import PageHeader from "../../components/layout/PageHeader";
import SectionCard from "../../components/layout/SectionCard";
import StatGrid from "../../components/layout/StatGrid";
import Card from "../../components/common/Card";
import DataTable from "../../components/common/DataTable";
import Button from "../../components/common/Button";
import Badge from "../../components/common/Badge";
import AreaChart from "../../components/charts/AreaChart";
import { ReportsAPI } from "../../api/reports";

const TABS = ["Platform", "Company", "Interview", "Candidate"];
const RANGES = ["Daily", "Weekly", "Monthly"];

export default function Reports() {
    const [tab, setTab] = useState("Platform");
    const [range, setRange] = useState("Monthly");
    const [stats, setStats] = useState(null);
    const [tabData, setTabData] = useState([]);
    const [chartData, setChartData] = useState([]);
    const [loading, setLoading] = useState(true);
    const [exporting, setExporting] = useState(false);

    useEffect(() => {
        const fetchReports = async () => {
            setLoading(true);
            try {
                const rangeFilter = range.toLowerCase();
                const chart = await ReportsAPI.getInterviewsChart(rangeFilter);
                setChartData(chart);
                
                if (tab === "Platform") {
                    const data = await ReportsAPI.getPlatformReport(rangeFilter);
                    setStats(data);
                } else if (tab === "Company") {
                    const data = await ReportsAPI.getCompanyReport(rangeFilter);
                    setTabData(data);
                } else if (tab === "Interview") {
                    const data = await ReportsAPI.getInterviewReport(rangeFilter);
                    setStats(data);
                } else if (tab === "Candidate") {
                    const data = await ReportsAPI.getCandidateReport(rangeFilter);
                    setTabData(data);
                }
            } catch (err) {
                console.error(err);
            } finally {
                setLoading(false);
            }
        };
        fetchReports();
    }, [tab, range]);

    const handleExportCSV = async () => {
        setExporting(true);
        try {
            await ReportsAPI.exportCSV(tab.toLowerCase(), range.toLowerCase());
        } catch (e) {
            console.error(e);
        } finally {
            setExporting(false);
        }
    };

    const handleExportPDF = async () => {
        setExporting(true);
        try {
            await ReportsAPI.exportPDF(tab.toLowerCase(), range.toLowerCase());
        } catch (e) {
            console.error(e);
        } finally {
            setExporting(false);
        }
    };

    const companyColumns = [
        { title: "Company", dataIndex: "company", sortable: true, render: (val) => <strong style={{ color: 'var(--text)' }}>{val}</strong> },
        { title: "Candidates", dataIndex: "candidates", sortable: true, align: "right" },
        { title: "Recruiters", dataIndex: "recruiters", sortable: true, align: "right" },
        { title: "Interviews", dataIndex: "interviews", sortable: true, align: "right" },
        { title: "Completions", dataIndex: "completions", sortable: true, align: "right" },
        { title: "Completion Rate", dataIndex: "completion", sortable: true, align: "right", render: (val) => (
            <Badge variant={val === '—' ? 'primary' : parseInt(val) >= 90 ? 'success' : parseInt(val) >= 75 ? 'warning' : 'danger'}>{val}</Badge>
        )},
    ];

    const candidateColumns = [
        { title: "Candidate", dataIndex: "candidate", sortable: true },
        { title: "Status", dataIndex: "status", sortable: true, render: (val) => <Badge variant="primary">{val}</Badge> },
        { title: "Resume Score", dataIndex: "resume_score", sortable: true, align: "right" },
        { title: "Interview Score", dataIndex: "interview_score", sortable: true, align: "right" },
    ];

    return (
        <DashboardGrid>
            <PageHeader
                title="Reports"
                description="Platform, company, interview and candidate reports across all time ranges."
                rightContent={
                    <div style={{ display: 'flex', gap: '10px' }}>
                        <Button variant="outline" onClick={handleExportPDF} disabled={exporting}><Download size={16} /> Export PDF</Button>
                        <Button variant="primary" onClick={handleExportCSV} disabled={exporting}><Download size={16} /> Export CSV</Button>
                    </div>
                }
            />

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div style={{ display: 'flex', gap: '4px', background: 'var(--surface)', padding: '4px', borderRadius: '10px', border: '1px solid var(--border)' }}>
                    {TABS.map(t => (
                        <button key={t} onClick={() => setTab(t)} style={{
                            padding: '7px 18px', borderRadius: '7px', border: 'none', cursor: 'pointer',
                            background: tab === t ? 'var(--card)' : 'transparent',
                            color: tab === t ? 'var(--text)' : 'var(--text-secondary)',
                            fontWeight: tab === t ? '600' : '400', fontSize: '14px',
                            boxShadow: tab === t ? 'var(--shadow)' : 'none',
                            transition: 'all 0.15s ease'
                        }}>{t}</button>
                    ))}
                </div>
                <div style={{ display: 'flex', gap: '4px' }}>
                    {RANGES.map(r => (
                        <button key={r} onClick={() => setRange(r)} style={{
                            padding: '6px 14px', borderRadius: '8px', border: '1px solid var(--border)',
                            background: range === r ? 'var(--primary)' : 'transparent',
                            color: range === r ? 'white' : 'var(--text-secondary)',
                            cursor: 'pointer', fontSize: '13px', fontWeight: '500',
                            transition: 'all 0.15s ease'
                        }}>{r}</button>
                    ))}
                </div>
            </div>

            {(tab === "Platform" || tab === "Interview") && (
                <StatGrid>
                    {tab === "Platform" ? [
                        { label: "Total Companies", value: stats ? stats.companies : 0 },
                        { label: "Total Recruiters", value: stats ? stats.recruiters : 0 },
                        { label: "Total Candidates", value: stats ? stats.candidates : 0 },
                        { label: "Active Interviews", value: stats ? stats.active_interviews : 0 },
                    ].map(({ label, value }) => (
                        <Card key={label} className="ih-card">
                            <div style={{ color: 'var(--text-secondary)', fontSize: '13px', marginBottom: '8px' }}>{label}</div>
                            <div style={{ fontSize: '28px', fontWeight: 'bold', color: 'var(--text)', display: 'flex', alignItems: 'baseline', gap: '8px' }}>
                                {loading ? "..." : value}
                            </div>
                        </Card>
                    )) : [
                        { label: "Interview Count", value: stats ? stats.interview_count : 0 },
                        { label: "Completed", value: stats ? stats.completed : 0 },
                        { label: "Cancelled", value: stats ? stats.cancelled : 0 },
                        { label: "Avg Duration", value: stats ? `${stats.average_duration}m` : "0m" },
                    ].map(({ label, value }) => (
                        <Card key={label} className="ih-card">
                            <div style={{ color: 'var(--text-secondary)', fontSize: '13px', marginBottom: '8px' }}>{label}</div>
                            <div style={{ fontSize: '28px', fontWeight: 'bold', color: 'var(--text)', display: 'flex', alignItems: 'baseline', gap: '8px' }}>
                                {loading ? "..." : value}
                            </div>
                        </Card>
                    ))}
                </StatGrid>
            )}

            <SectionCard>
                <h3 style={{ fontSize: '15px', fontWeight: '600', color: 'var(--text)', padding: '20px 24px 0', marginBottom: '16px' }}>Interview Activity</h3>
                <div style={{ padding: '0 24px 24px' }}>
                    {!loading && chartData.length === 0 ? (
                        <div style={{ height: 260, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)' }}>No chart data available.</div>
                    ) : (
                        <AreaChart
                            data={chartData}
                            xAxisKey="name"
                            series={[
                                { key: "completed", color: "#22c55e", label: "Completed" },
                                { key: "scheduled", color: "#2563EB", label: "Scheduled" },
                                { key: "cancelled", color: "#ef4444", label: "Cancelled" },
                            ]}
                            height={260}
                        />
                    )}
                </div>
            </SectionCard>

            {tab === "Company" && (
                <SectionCard>
                    <h3 style={{ fontSize: '15px', fontWeight: '600', color: 'var(--text)', padding: '20px 24px 16px' }}>Company Report</h3>
                    {loading ? <div style={{ padding: '24px', textAlign: 'center' }}>Loading...</div> : (
                        tabData.length === 0 ? <div style={{ padding: '24px', textAlign: 'center', color: 'var(--text-muted)' }}>No reports available.</div> : <DataTable columns={companyColumns} data={tabData} keyField="id" searchable={true} />
                    )}
                </SectionCard>
            )}

            {tab === "Candidate" && (
                <SectionCard>
                    <h3 style={{ fontSize: '15px', fontWeight: '600', color: 'var(--text)', padding: '20px 24px 16px' }}>Candidate Report</h3>
                    {loading ? <div style={{ padding: '24px', textAlign: 'center' }}>Loading...</div> : (
                        tabData.length === 0 ? <div style={{ padding: '24px', textAlign: 'center', color: 'var(--text-muted)' }}>No reports available.</div> : <DataTable columns={candidateColumns} data={tabData} keyField="id" searchable={true} />
                    )}
                </SectionCard>
            )}
        </DashboardGrid>
    );
}
