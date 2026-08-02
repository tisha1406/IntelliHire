import { useState, useEffect } from "react";
import { RefreshCw, Activity, Server, Database, Cloud } from "lucide-react";
import DashboardGrid from "../../layouts/DashboardGrid";
import PageHeader from "../../components/layout/PageHeader";
import SectionCard from "../../components/layout/SectionCard";
import StatGrid from "../../components/layout/StatGrid";
import Card from "../../components/common/Card";
import Button from "../../components/common/Button";
import Badge from "../../components/common/Badge";
import { SystemAPI } from "../../api/system";

export default function SystemHealth() {
    const [health, setHealth] = useState(null);
    const [loading, setLoading] = useState(true);

    const fetchHealth = async () => {
        setLoading(true);
        try {
            const data = await SystemAPI.getHealth();
            setHealth(data);
        } catch (err) {
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchHealth();
    }, []);

    const rightContent = (
        <div style={{ display: 'flex', gap: '12px' }}>
            <Button variant="outline" onClick={fetchHealth}>
                <RefreshCw size={16} />
                Refresh Status
            </Button>
        </div>
    );

    const statusPill = (status) => {
        let variant = 'success';
        if (status === 'degraded') variant = 'warning';
        if (status === 'outage') variant = 'danger';
        return <Badge variant={variant}>{status === 'healthy' ? 'Operational' : status}</Badge>;
    };

    return (
        <DashboardGrid>
            <PageHeader 
                title="System Health"
                description="Real-time monitoring for AI infrastructure, backend services, and APIs."
                rightContent={rightContent}
            />

            <StatGrid>
                <Card className="ih-card">
                    <div style={{ color: 'var(--text-secondary)', fontSize: '13px', marginBottom: '8px', display: 'flex', justifyContent: 'space-between' }}>
                        CPU Usage
                        <Activity size={16} style={{ color: 'var(--success)' }} />
                    </div>
                    <div style={{ fontSize: '28px', fontWeight: 'bold', color: 'var(--text)' }}>
                        {loading ? "..." : `${health?.cpu_usage || 0}%`}
                    </div>
                </Card>
                <Card className="ih-card">
                    <div style={{ color: 'var(--text-secondary)', fontSize: '13px', marginBottom: '8px', display: 'flex', justifyContent: 'space-between' }}>
                        Memory Usage
                        <Server size={16} style={{ color: 'var(--primary)' }} />
                    </div>
                    <div style={{ fontSize: '28px', fontWeight: 'bold', color: 'var(--text)' }}>
                        {loading ? "..." : `${health?.memory_percent || 0}%`}
                    </div>
                </Card>
                <Card className="ih-card">
                    <div style={{ color: 'var(--text-secondary)', fontSize: '13px', marginBottom: '8px', display: 'flex', justifyContent: 'space-between' }}>
                        Disk Usage
                        <Database size={16} style={{ color: 'var(--text)' }} />
                    </div>
                    <div style={{ fontSize: '28px', fontWeight: 'bold', color: 'var(--text)' }}>
                        {loading ? "..." : `${health?.disk_percent || 0}%`}
                    </div>
                </Card>
                <Card className="ih-card">
                    <div style={{ color: 'var(--text-secondary)', fontSize: '13px', marginBottom: '8px', display: 'flex', justifyContent: 'space-between' }}>
                        System Uptime
                        <Cloud size={16} style={{ color: 'var(--primary)' }} />
                    </div>
                    <div style={{ fontSize: '28px', fontWeight: 'bold', color: 'var(--text)' }}>
                        99.9%
                    </div>
                </Card>
            </StatGrid>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', gap: '20px', marginTop: '20px' }}>
                <SectionCard title="Backend Services">
                    {loading ? <div style={{ padding: '24px', textAlign: 'center' }}>Loading...</div> : (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingBottom: '16px', borderBottom: '1px solid var(--border-subtle)' }}>
                                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                                    <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: 'var(--success)' }}></div>
                                    <span style={{ color: 'var(--text)', fontWeight: '500' }}>FastAPI Backend</span>
                                </div>
                                {statusPill(health?.services?.fastapi || 'unknown')}
                            </div>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingBottom: '16px', borderBottom: '1px solid var(--border-subtle)' }}>
                                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                                    <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: 'var(--success)' }}></div>
                                    <span style={{ color: 'var(--text)', fontWeight: '500' }}>MongoDB Cluster</span>
                                </div>
                                {statusPill(health?.services?.mongodb || 'unknown')}
                            </div>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                                    <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: 'var(--success)' }}></div>
                                    <span style={{ color: 'var(--text)', fontWeight: '500' }}>Redis Cache</span>
                                </div>
                                {statusPill(health?.services?.redis || 'unknown')}
                            </div>
                        </div>
                    )}
                </SectionCard>

                <SectionCard title="AI Infrastructure">
                    {loading ? <div style={{ padding: '24px', textAlign: 'center' }}>Loading...</div> : (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingBottom: '16px', borderBottom: '1px solid var(--border-subtle)' }}>
                                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                                    <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: 'var(--success)' }}></div>
                                    <span style={{ color: 'var(--text)', fontWeight: '500' }}>Groq LPUs (Llama 3)</span>
                                </div>
                                {statusPill('healthy')}
                            </div>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingBottom: '16px', borderBottom: '1px solid var(--border-subtle)' }}>
                                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                                    <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: 'var(--success)' }}></div>
                                    <span style={{ color: 'var(--text)', fontWeight: '500' }}>Gemini (Multimodal API)</span>
                                </div>
                                {statusPill('healthy')}
                            </div>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingBottom: '16px', borderBottom: '1px solid var(--border-subtle)' }}>
                                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                                    <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: 'var(--warning)' }}></div>
                                    <span style={{ color: 'var(--text)', fontWeight: '500' }}>Sarvam AI (Indic Voice)</span>
                                </div>
                                {statusPill('degraded')}
                            </div>
                        </div>
                    )}
                </SectionCard>
            </div>
        </DashboardGrid>
    );
}