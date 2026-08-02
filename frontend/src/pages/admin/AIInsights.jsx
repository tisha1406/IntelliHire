import { useState, useEffect } from "react";
import DashboardGrid from "../../layouts/DashboardGrid";
import PageHeader from "../../components/layout/PageHeader";
import SectionCard from "../../components/layout/SectionCard";
import StatGrid from "../../components/layout/StatGrid";
import ContentGrid from "../../components/layout/ContentGrid";
import Card from "../../components/common/Card";
import Badge from "../../components/common/Badge";
import AreaChart from "../../components/charts/AreaChart";
import DonutChart from "../../components/charts/DonutChart";
import HorizontalBarChart from "../../components/charts/HorizontalBarChart";
import { AICenterAPI } from "../../api/ai_center";



export default function AIInsights() {
    const [usage, setUsage] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchUsage = async () => {
            try {
                const data = await AICenterAPI.getUsage();
                setUsage(data);
            } catch (err) {
                console.error(err);
            } finally {
                setLoading(false);
            }
        };
        fetchUsage();
    }, []);

    const kpis = [
        { label: "Total Tokens", value: usage ? usage.total_tokens?.toLocaleString() : "0", change: "0%", positive: true },
        { label: "Estimated Cost", value: usage ? `$${usage.cost_estimated?.toFixed(2)}` : "$0.00", change: "0%", positive: true },
        { label: "Avg Latency", value: usage ? `${usage.average_latency_ms}ms` : "0ms", change: "0%", positive: true },
        { label: "Fallback Triggered", value: "0", change: "0%", positive: true },
    ];

    const modelSplit = usage && usage.models_distribution && Object.keys(usage.models_distribution).length > 0 ? [
        { name: "GPT-4", value: usage.models_distribution["gpt-4"] || 0, color: "#2563EB" },
        { name: "Llama 3", value: usage.models_distribution["llama-3"] || 0, color: "#8B5CF6" },
        { name: "Gemini", value: usage.models_distribution["gemini"] || 0, color: "#06b6d4" },
    ] : [];

    return (
        <DashboardGrid>
            <PageHeader title="AI Insights" description="Platform-wide AI usage metrics, model performance, and token consumption analytics." />

            <StatGrid>
                {kpis.map(({ label, value, change, positive }) => (
                    <Card key={label} className="ih-card">
                        <div style={{ color: 'var(--text-secondary)', fontSize: '13px', marginBottom: '8px' }}>{label}</div>
                        <div style={{ fontSize: '28px', fontWeight: 'bold', color: 'var(--text)', display: 'flex', alignItems: 'baseline', gap: '8px' }}>
                            {loading ? "..." : value}
                            <span style={{ fontSize: '13px', fontWeight: '500', color: positive ? 'var(--success)' : 'var(--danger)' }}>{change}</span>
                        </div>
                    </Card>
                ))}
            </StatGrid>

            <SectionCard>
                <h3 style={{ fontSize: '15px', fontWeight: '600', color: 'var(--text)', marginBottom: '20px', padding: '20px 24px 0' }}>Token Consumption (Last 7 Days)</h3>
                <div style={{ padding: '0 24px 24px' }}>
                    {!loading && (!usage?.tokenData || usage.tokenData.length === 0) ? (
                        <div style={{ height: 260, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)' }}>No token data available yet.</div>
                    ) : (
                        <AreaChart
                            data={usage?.tokenData || []}
                            xAxisKey="name"
                            series={[
                                { key: "tokens", color: "#2563EB", label: "Tokens" },
                            ]}
                            height={260}
                        />
                    )}
                </div>
            </SectionCard>

            <ContentGrid>
                <div className="main-content">
                    <SectionCard>
                        <h3 style={{ fontSize: '15px', fontWeight: '600', color: 'var(--text)', marginBottom: '20px', padding: '20px 24px 0' }}>Token Usage by Company</h3>
                        <div style={{ padding: '0 24px 24px' }}>
                            {!loading && (!usage?.companyUsage || usage.companyUsage.length === 0) ? (
                                <div style={{ height: 260, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)' }}>No usage data available yet.</div>
                            ) : (
                                <HorizontalBarChart data={usage?.companyUsage || []} nameKey="name" valueKey="value" height={260} />
                            )}
                        </div>
                    </SectionCard>
                </div>
                <div className="side-content">
                    <SectionCard>
                        <h3 style={{ fontSize: '15px', fontWeight: '600', color: 'var(--text)', marginBottom: '4px', padding: '20px 24px 0' }}>Model Distribution</h3>
                        <div style={{ padding: '0 24px 24px' }}>
                            {loading ? <div style={{height: 280, display: 'flex', alignItems:'center', justifyContent:'center'}}>Loading...</div> : modelSplit.length === 0 ? <div style={{height: 280, display: 'flex', alignItems:'center', justifyContent:'center', color: 'var(--text-muted)'}}>No model distribution data.</div> : <DonutChart data={modelSplit} height={280} />}
                        </div>
                    </SectionCard>
                </div>
            </ContentGrid>

            <SectionCard>
                <h3 style={{ fontSize: '15px', fontWeight: '600', color: 'var(--text)', padding: '20px 24px 16px' }}>Model Performance</h3>
                <div style={{ padding: '0 24px 24px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
                    {!loading && (!usage?.models || usage.models.length === 0) ? (
                        <div style={{ height: 100, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)' }}>No model performance metrics available.</div>
                    ) : (
                        (usage?.models || []).map(m => (
                            <div key={m.model} style={{ display: 'grid', gridTemplateColumns: '1fr auto auto auto auto', alignItems: 'center', gap: '24px', padding: '14px 16px', background: 'var(--surface)', borderRadius: '8px', border: '1px solid var(--border)' }}>
                                <div>
                                    <strong style={{ color: 'var(--text)', display: 'block' }}>{m.model}</strong>
                                    <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>{m.requests} requests today</span>
                                </div>
                                <div style={{ textAlign: 'right' }}>
                                    <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Accuracy</div>
                                    <strong style={{ color: m.accuracy >= 90 ? 'var(--success)' : 'var(--warning)' }}>{m.accuracy}%</strong>
                                </div>
                                <div style={{ textAlign: 'right' }}>
                                    <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Avg Latency</div>
                                    <strong style={{ color: 'var(--text)' }}>{m.latency}</strong>
                                </div>
                                <Badge variant={m.status === 'Operational' ? 'success' : 'warning'}>{m.status}</Badge>
                            </div>
                        ))
                    )}
                </div>
            </SectionCard>
        </DashboardGrid>
    );
}
