import { useState, useEffect } from "react";
import DashboardGrid from "../../layouts/DashboardGrid";
import PageHeader from "../../components/layout/PageHeader";
import SectionCard from "../../components/layout/SectionCard";
import StatGrid from "../../components/layout/StatGrid";
import ContentGrid from "../../components/layout/ContentGrid";
import Card from "../../components/common/Card";
import DataTable from "../../components/common/DataTable";
import Badge from "../../components/common/Badge";
import AreaChart from "../../components/charts/AreaChart";
import HorizontalBarChart from "../../components/charts/HorizontalBarChart";
import DonutChart from "../../components/charts/DonutChart";
import { AICenterAPI } from "../../api/ai_center";



export default function InterviewAnalysis() {
    const [summary, setSummary] = useState(null);
    const [records, setRecords] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchAnalysis = async () => {
            setLoading(true);
            try {
                const [summaryData, recordsData] = await Promise.all([
                    AICenterAPI.getInterviewAnalysis(),
                    AICenterAPI.getInterviewAnalysisRecords({ limit: 100 })
                ]);
                setSummary(summaryData);
                setRecords(recordsData);
            } catch (err) {
                console.error(err);
            } finally {
                setLoading(false);
            }
        };
        fetchAnalysis();
    }, []);

    const qColumns = [
        { title: "Candidate", dataIndex: "candidate_name", sortable: true },
        { title: "Campaign", dataIndex: "campaign", sortable: true },
        { title: "Score", dataIndex: "score", sortable: true, align: "right", render: (val) => <strong>{val}%</strong> },
        { title: "AI Confidence", dataIndex: "ai_confidence", sortable: true, align: "right", render: (val) => <strong>{val}%</strong> },
        { title: "Date", dataIndex: "created_at", sortable: true, align: "right", render: (val) => new Date(val).toLocaleDateString() },
    ];

    const difficultyData = summary && summary.difficulty_distribution ? [
        { name: "Easy", value: summary.difficulty_distribution.easy || 0, color: "#22c55e" },
        { name: "Medium", value: summary.difficulty_distribution.medium || 0, color: "#f59e0b" },
        { name: "Hard", value: summary.difficulty_distribution.hard || 0, color: "#ef4444" },
    ] : [];

    return (
        <DashboardGrid>
            <PageHeader title="Interview Analysis" description="Platform-wide analytics on question coverage, skill assessments, and AI evaluation quality." />

            <StatGrid>
                {[
                    { label: "Avg Score", value: summary ? `${summary.average_score}%` : "0%", color: "var(--primary)" },
                    { label: "Avg Communication", value: summary && summary.skill_distribution ? `${summary.skill_distribution.communication}%` : "0%", color: "#8B5CF6" },
                    { label: "Avg Technical", value: summary && summary.skill_distribution ? `${summary.skill_distribution.technical}%` : "0%", color: "var(--success)" },
                    { label: "Avg Problem Solving", value: summary && summary.skill_distribution ? `${summary.skill_distribution.problem_solving}%` : "0%", color: "var(--warning)" },
                ].map(({ label, value, color }) => (
                    <Card key={label} className="ih-card">
                        <div style={{ color: 'var(--text-secondary)', fontSize: '13px', marginBottom: '8px' }}>{label}</div>
                        <div style={{ fontSize: '28px', fontWeight: 'bold', color }}>{loading ? "..." : value}</div>
                    </Card>
                ))}
            </StatGrid>

            <SectionCard>
                <h3 style={{ fontSize: '15px', fontWeight: '600', color: 'var(--text)', padding: '20px 24px 0', marginBottom: '16px' }}>Weekly Skill Score Trends</h3>
                <div style={{ padding: '0 24px 24px' }}>
                    {!loading && (!summary?.weeklyData || summary.weeklyData.length === 0) ? (
                        <div style={{ height: 260, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)' }}>No trend data available.</div>
                    ) : (
                        <AreaChart
                            data={summary?.weeklyData || []}
                            xAxisKey="name"
                            series={[
                                { key: "technical", color: "#2563EB", label: "Technical" },
                                { key: "communication", color: "#8B5CF6", label: "Communication" },
                                { key: "behavior", color: "#22c55e", label: "Behavioral" },
                            ]}
                            height={260}
                        />
                    )}
                </div>
            </SectionCard>

            <ContentGrid>
                <div className="main-content">
                    <SectionCard>
                        <h3 style={{ fontSize: '15px', fontWeight: '600', color: 'var(--text)', padding: '20px 24px 0', marginBottom: '4px' }}>Top Question Coverage Areas</h3>
                        <div style={{ padding: '0 24px 24px' }}>
                            {!loading && (!summary?.coverageData || summary.coverageData.length === 0) ? (
                                <div style={{ height: 220, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)' }}>No coverage data available.</div>
                            ) : (
                                <HorizontalBarChart data={summary?.coverageData || []} nameKey="name" valueKey="value" height={220} />
                            )}
                        </div>
                    </SectionCard>
                </div>
                <div className="side-content">
                    <SectionCard>
                        <h3 style={{ fontSize: '15px', fontWeight: '600', color: 'var(--text)', padding: '20px 24px 0', marginBottom: '4px' }}>Question Difficulty</h3>
                        <div style={{ padding: '0 24px 24px' }}>
                            {loading ? <div style={{height: 240, display: 'flex', alignItems:'center', justifyContent:'center'}}>Loading...</div> : difficultyData.length === 0 || difficultyData.every(d => d.value === 0) ? <div style={{height: 240, display: 'flex', alignItems:'center', justifyContent:'center', color: 'var(--text-muted)'}}>No difficulty data.</div> : <DonutChart data={difficultyData} height={240} />}
                        </div>
                    </SectionCard>
                </div>
            </ContentGrid>

            <SectionCard>
                <h3 style={{ fontSize: '15px', fontWeight: '600', color: 'var(--text)', padding: '20px 24px 16px' }}>Interview Analysis Records</h3>
                <div style={{ padding: '0 0 8px' }}>
                    {loading ? <div style={{ padding: '24px', textAlign: 'center' }}>Loading...</div> : (
                        <DataTable columns={qColumns} data={records} keyField="id" searchable={true} />
                    )}
                </div>
            </SectionCard>
        </DashboardGrid>
    );
}
