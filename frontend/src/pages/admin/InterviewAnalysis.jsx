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
        { title: "Date", dataIndex: "created_at", sortable: true, align: "right", render: (val) => new Date(val).toLocaleDateString() },
    ];

    const difficultyData = summary && summary.difficulty_distribution ? [
        { name: "Easy", value: summary.difficulty_distribution.easy || 0, color: "#22c55e" },
        { name: "Medium", value: summary.difficulty_distribution.medium || 0, color: "#f59e0b" },
        { name: "Hard", value: summary.difficulty_distribution.hard || 0, color: "#ef4444" },
    ] : [];

    // Extract top 3 topics for StatGrid
    const topTopics = summary?.top_topics || [];
    const statCards = [
        { label: "Overall Average Score", value: summary ? `${summary.average_score}%` : "0%", color: "var(--primary)" },
    ];
    
    // Add up to 3 topics
    const colors = ["#8B5CF6", "var(--success)", "var(--warning)"];
    for (let i = 0; i < Math.min(3, topTopics.length); i++) {
        statCards.push({
            label: `Top Topic: ${topTopics[i].topic_name}`,
            value: `${topTopics[i].average_score}%`,
            color: colors[i]
        });
    }
    
    // If we have less than 4 cards, fill the rest with placeholders to maintain grid
    while (statCards.length < 4) {
        statCards.push({ label: "—", value: "—", color: "var(--text-muted)" });
    }

    return (
        <DashboardGrid>
            <PageHeader title="Interview Analysis" description="Platform-wide analytics on question coverage, skill assessments, and AI evaluation quality." />

            <StatGrid>
                {statCards.map(({ label, value, color }, idx) => (
                    <Card key={idx} className="ih-card">
                        <div style={{ color: 'var(--text-secondary)', fontSize: '13px', marginBottom: '8px' }}>{label}</div>
                        <div style={{ fontSize: '28px', fontWeight: 'bold', color }}>{loading ? "..." : value}</div>
                    </Card>
                ))}
            </StatGrid>

            <ContentGrid>
                <div className="main-content">
                    <SectionCard>
                        <h3 style={{ fontSize: '15px', fontWeight: '600', color: 'var(--text)', padding: '20px 24px 0', marginBottom: '4px' }}>Top Topics by Performance</h3>
                        <div style={{ padding: '0 24px 24px' }}>
                            {!loading && topTopics.length === 0 ? (
                                <div style={{ height: 260, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)' }}>No topic data available.</div>
                            ) : (
                                <HorizontalBarChart 
                                    data={topTopics.map(t => ({ name: t.topic_name, value: t.average_score }))} 
                                    nameKey="name" 
                                    valueKey="value" 
                                    height={260} 
                                />
                            )}
                        </div>
                    </SectionCard>
                </div>
                <div className="side-content">
                    <SectionCard>
                        <h3 style={{ fontSize: '15px', fontWeight: '600', color: 'var(--text)', padding: '20px 24px 0', marginBottom: '4px' }}>Question Difficulty</h3>
                        <div style={{ padding: '0 24px 24px' }}>
                            {loading ? <div style={{height: 260, display: 'flex', alignItems:'center', justifyContent:'center'}}>Loading...</div> : difficultyData.length === 0 || difficultyData.every(d => d.value === 0) ? <div style={{height: 260, display: 'flex', alignItems:'center', justifyContent:'center', color: 'var(--text-muted)'}}>No difficulty data.</div> : <DonutChart data={difficultyData} height={260} />}
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
