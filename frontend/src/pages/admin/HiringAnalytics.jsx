import { useState, useEffect } from "react";
import DashboardGrid from "../../layouts/DashboardGrid";
import PageHeader from "../../components/layout/PageHeader";
import SectionCard from "../../components/layout/SectionCard";
import StatGrid from "../../components/layout/StatGrid";
import ContentGrid from "../../components/layout/ContentGrid";
import Card from "../../components/common/Card";
import DataTable from "../../components/common/DataTable";
import Badge from "../../components/common/Badge";
import LineChart from "../../components/charts/LineChart";
import DonutChart from "../../components/charts/DonutChart";
import HorizontalBarChart from "../../components/charts/HorizontalBarChart";
import { AnalyticsAPI } from "../../api/analytics";



export default function HiringAnalytics() {
    const [hiringData, setHiringData] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchHiring = async () => {
            try {
                const data = await AnalyticsAPI.getHiringAnalytics();
                setHiringData(data);
            } catch (err) {
                console.error(err);
            } finally {
                setLoading(false);
            }
        };
        fetchHiring();
    }, []);

    const companyColumns = [
        { title: "Company", dataIndex: "company", sortable: true, render: (val) => <strong style={{ color: 'var(--text)' }}>{val}</strong> },
        { title: "Invited", dataIndex: "invited", sortable: true, align: "right" },
        { title: "Completed", dataIndex: "completed", sortable: true, align: "right" },
        { title: "Shortlisted", dataIndex: "shortlisted", sortable: true, align: "right" },
        { title: "Offered", dataIndex: "offered", sortable: true, align: "right" },
        { title: "Offer Rate", dataIndex: "offerRate", sortable: true, align: "right", render: (val) => <Badge variant="primary">{val}</Badge> },
    ];

    const funnelData = hiringData?.funnel ? [
        { stage: "Applications Received", count: hiringData.funnel.invited || 0, pct: 100 }, 
        { stage: "Resume Screened (Pass)", count: hiringData.funnel.started || 0, pct: hiringData.funnel.invited ? Math.round((hiringData.funnel.started / hiringData.funnel.invited) * 100) : 0 }, 
        { stage: "Interview Completed", count: hiringData.funnel.completed || 0, pct: hiringData.funnel.invited ? Math.round((hiringData.funnel.completed / hiringData.funnel.invited) * 100) : 0 },
        { stage: "Shortlisted", count: hiringData.funnel.passed || 0, pct: hiringData.funnel.invited ? Math.round((hiringData.funnel.passed / hiringData.funnel.invited) * 100) : 0 },
        { stage: "Offered", count: hiringData.funnel.hired || 0, pct: hiringData.funnel.invited ? Math.round((hiringData.funnel.hired / hiringData.funnel.invited) * 100) : 0 },
    ] : [];

    return (
        <DashboardGrid>
            <PageHeader title="Hiring Analytics" description="End-to-end hiring funnel metrics, offer rates, and cross-company performance comparison." />

            <StatGrid>
                {[
                    { label: "Total Applicants", value: hiringData?.funnel?.invited ? hiringData.funnel.invited.toLocaleString() : "0", color: "var(--text)" },
                    { label: "Completion Rate", value: hiringData?.funnel?.completed && hiringData?.funnel?.invited ? `${Math.round((hiringData.funnel.completed / hiringData.funnel.invited) * 100)}%` : "0%", color: "var(--success)" },
                    { label: "Selection Rate", value: hiringData?.funnel?.passed && hiringData?.funnel?.completed ? `${Math.round((hiringData.funnel.passed / hiringData.funnel.completed) * 100)}%` : "0%", color: "var(--primary)" },
                    { label: "Time to Hire", value: hiringData?.time_to_hire_days ? `${hiringData.time_to_hire_days} days` : "0", color: "#8B5CF6" },
                ].map(({ label, value, color }) => (
                    <Card key={label} className="ih-card">
                        <div style={{ color: 'var(--text-secondary)', fontSize: '13px', marginBottom: '8px' }}>{label}</div>
                        <div style={{ fontSize: '28px', fontWeight: 'bold', color }}>{loading ? "..." : value}</div>
                    </Card>
                ))}
            </StatGrid>

            <SectionCard>
                <h3 style={{ fontSize: '15px', fontWeight: '600', color: 'var(--text)', padding: '20px 24px 0', marginBottom: '8px' }}>Hiring Funnel</h3>
                <div style={{ padding: '0 24px 24px', display: 'flex', flexDirection: 'column', gap: '10px' }}>
                    {loading ? <div style={{ padding: '24px', textAlign: 'center' }}>Loading...</div> : funnelData.map((stage, i) => (
                        <div key={stage.stage} style={{ display: 'grid', gridTemplateColumns: '220px 1fr 60px', gap: '16px', alignItems: 'center' }}>
                            <span style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>{stage.stage}</span>
                            <div style={{ height: '20px', background: 'var(--border)', borderRadius: '4px', overflow: 'hidden' }}>
                                <div style={{
                                    height: '100%',
                                    width: `${stage.pct}%`,
                                    background: `hsl(${220 + i * 20}, 70%, ${55 - i * 4}%)`,
                                    borderRadius: '4px',
                                    transition: 'width 0.6s ease',
                                    display: 'flex', alignItems: 'center', paddingLeft: '8px'
                                }}>
                                    <span style={{ fontSize: '11px', fontWeight: '600', color: 'white' }}>{stage.count.toLocaleString()}</span>
                                </div>
                            </div>
                            <span style={{ fontSize: '13px', fontWeight: '600', color: 'var(--text)', textAlign: 'right' }}>{stage.pct}%</span>
                        </div>
                    ))}
                </div>
            </SectionCard>

            <ContentGrid>
                <div className="main-content">
                    <SectionCard>
                        <h3 style={{ fontSize: '15px', fontWeight: '600', color: 'var(--text)', padding: '20px 24px 0', marginBottom: '8px' }}>Interview Trends (Monthly)</h3>
                        <div style={{ padding: '0 24px 24px' }}>
                            {!loading && (!hiringData?.trendData || hiringData.trendData.length === 0) ? (
                                <div style={{ height: 260, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)' }}>No trend data available yet.</div>
                            ) : (
                                <LineChart
                                    data={hiringData?.trendData || []}
                                    xAxisKey="name"
                                    series={[
                                        { key: "invited", color: "#2563EB", label: "Invited" },
                                        { key: "completions", color: "#22c55e", label: "Completions" },
                                        { key: "offers", color: "#f59e0b", label: "Offers" },
                                    ]}
                                    height={260}
                                    showLegend={true}
                                />
                            )}
                        </div>
                    </SectionCard>
                </div>
                <div className="side-content">
                    <SectionCard>
                        <h3 style={{ fontSize: '15px', fontWeight: '600', color: 'var(--text)', padding: '20px 24px 0', marginBottom: '4px' }}>By Interview Mode</h3>
                        <div style={{ padding: '0 24px 24px' }}>
                            {!loading && (!hiringData?.modeBreakdown || hiringData.modeBreakdown.length === 0) ? (
                                <div style={{ height: 260, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)' }}>No interview mode data.</div>
                            ) : (
                                <DonutChart data={hiringData?.modeBreakdown || []} height={260} />
                            )}
                        </div>
                    </SectionCard>
                </div>
            </ContentGrid>

            <SectionCard>
                <h3 style={{ fontSize: '15px', fontWeight: '600', color: 'var(--text)', padding: '20px 24px 16px' }}>Company Comparison</h3>
                {loading ? <div style={{ padding: '24px', textAlign: 'center' }}>Loading...</div> : (
                    <DataTable columns={companyColumns} data={hiringData?.companyComparison || []} keyField="id" />
                )}
            </SectionCard>
        </DashboardGrid>
    );
}
