import { useState, useEffect } from "react";
import { RefreshCw } from "lucide-react";
import DashboardGrid from "../../layouts/DashboardGrid";
import PageHeader from "../../components/layout/PageHeader";
import SectionCard from "../../components/layout/SectionCard";
import StatGrid from "../../components/layout/StatGrid";
import ContentGrid from "../../components/layout/ContentGrid";
import Card from "../../components/common/Card";
import Button from "../../components/common/Button";
import Badge from "../../components/common/Badge";
import LineChart from "../../components/charts/LineChart";
import RadialProgressChart from "../../components/charts/RadialProgressChart";
import { AnalyticsAPI } from "../../api/analytics";



export default function Performance() {
    const [metrics, setMetrics] = useState(null);
    const [loading, setLoading] = useState(true);

    const fetchMetrics = async () => {
        setLoading(true);
        try {
            const data = await AnalyticsAPI.getPerformanceMetrics();
            setMetrics(data);
        } catch (err) {
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchMetrics();
    }, []);

    const systemMetrics = [
        { label: "CPU Usage", value: metrics?.cpu_usage || 0, max: 100, color: "#2563EB" },
        { label: "Memory Usage", value: metrics?.memory_usage || 0, max: 100, color: "#8B5CF6" },
        { label: "Storage", value: metrics?.storage_usage || 0, max: 100, color: "#22c55e" },
        { label: "Model Accuracy", value: metrics?.model_accuracy || 0, max: 100, color: "#f59e0b" },
    ];

    return (
        <DashboardGrid>
            <PageHeader
                title="Performance"
                description="Real-time platform performance monitoring — API latency, throughput, model accuracy, and resource utilization."
                rightContent={<Button variant="outline" onClick={fetchMetrics}><RefreshCw size={16} /> Refresh</Button>}
            />

            <StatGrid>
                {[
                    { label: "API Avg Response", value: metrics ? `${metrics.api_latency_ms}ms` : "0ms", status: "Healthy" },
                    { label: "Error Rate", value: metrics ? `${metrics.error_rate_percentage}%` : "0%", status: "Healthy" },
                    { label: "Peak Concurrent", value: metrics ? `${metrics.concurrent_interviews_peak}` : "0", status: "Healthy" },
                    { label: "Uptime", value: metrics ? `${metrics.uptime_percentage}%` : "0%", status: "Healthy" },
                ].map(({ label, value, status }) => (
                    <Card key={label} className="ih-card">
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '8px' }}>
                            <div style={{ color: 'var(--text-secondary)', fontSize: '13px' }}>{label}</div>
                            <Badge variant="success">{status}</Badge>
                        </div>
                        <div style={{ fontSize: '26px', fontWeight: 'bold', color: 'var(--text)' }}>{loading ? "..." : value}</div>
                    </Card>
                ))}
            </StatGrid>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '20px' }}>
                {systemMetrics.map(m => (
                    <Card key={m.label} className="ih-card" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', padding: '24px' }}>
                        <RadialProgressChart value={m.value} max={m.max} size={120} color={m.color} label={m.label} />
                    </Card>
                ))}
            </div>

            <SectionCard>
                <h3 style={{ fontSize: '15px', fontWeight: '600', color: 'var(--text)', padding: '20px 24px 0', marginBottom: '8px' }}>Response Time (Last 6 Hours)</h3>
                <div style={{ padding: '0 24px 24px' }}>
                    {!loading && (!metrics?.responseTimeData || metrics.responseTimeData.length === 0) ? (
                        <div style={{ height: 260, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)' }}>No response time data available yet.</div>
                    ) : (
                        <LineChart
                            data={metrics?.responseTimeData || []}
                            xAxisKey="name"
                            series={[
                                { key: "api", color: "#2563EB", label: "API (ms)" },
                                { key: "processing", color: "#8B5CF6", label: "Processing (ms)" },
                            ]}
                            height={260}
                            showLegend={true}
                        />
                    )}
                </div>
            </SectionCard>

            <SectionCard>
                <h3 style={{ fontSize: '15px', fontWeight: '600', color: 'var(--text)', padding: '20px 24px 8px' }}>Service Status</h3>
                <div style={{ padding: '0 24px 24px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
                    {!loading && (!metrics?.services || metrics.services.length === 0) ? (
                        <div style={{ padding: '24px', textAlign: 'center', color: 'var(--text-muted)' }}>No services data available.</div>
                    ) : (
                        (metrics?.services || []).map(s => (
                            <div key={s.name} style={{ display: 'grid', gridTemplateColumns: '1fr auto auto auto', alignItems: 'center', gap: '24px', padding: '14px 16px', background: 'var(--surface)', borderRadius: '8px', border: '1px solid var(--border)' }}>
                                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                                    <div style={{ width: '10px', height: '10px', borderRadius: '50%', background: s.status === 'Operational' ? 'var(--success)' : 'var(--warning)', boxShadow: `0 0 6px ${s.status === 'Operational' ? 'var(--success)' : 'var(--warning)'}` }} />
                                    <strong style={{ color: 'var(--text)' }}>{s.name}</strong>
                                </div>
                                <div style={{ textAlign: 'right' }}>
                                    <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Latency</div>
                                    <code style={{ fontSize: '13px', color: 'var(--text)', fontWeight: '600' }}>{s.latency}</code>
                                </div>
                                <div style={{ textAlign: 'right' }}>
                                    <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Uptime</div>
                                    <strong style={{ color: s.status === 'Operational' ? 'var(--success)' : 'var(--warning)', fontSize: '13px' }}>{s.uptime}</strong>
                                </div>
                                <Badge variant={s.status === 'Operational' ? 'success' : 'warning'}>{s.status}</Badge>
                            </div>
                        ))
                    )}
                </div>
            </SectionCard>
        </DashboardGrid>
    );
}
