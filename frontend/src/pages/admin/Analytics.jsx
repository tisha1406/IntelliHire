import {
    BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area
} from "recharts";
import DashboardGrid from "../../layouts/DashboardGrid";
import PageHeader from "../../components/layout/PageHeader";
import StatGrid from "../../components/layout/StatGrid";
import SectionCard from "../../components/layout/SectionCard";
import Card from "../../components/common/Card";
import { useAdminAnalytics } from "../../hooks/useAdminAnalytics";

function StatValue({ loading, value }) {
    if (loading) {
        return <span style={{ color: 'var(--text-secondary)' }}>—</span>;
    }
    return value;
}

export default function Analytics() {
    const { data, isLoading, error } = useAdminAnalytics();

    const kpis = data?.kpis || {};
    const interviewsOverTime = data?.charts?.interviews_over_time || [];
    const companyGrowth = data?.charts?.company_growth || [];

    return (
        <DashboardGrid>
            <PageHeader
                title="Platform Analytics"
                description="Comprehensive metrics across all companies and candidates."
            />

            {error && (
                <div style={{ color: 'var(--danger)', marginBottom: '16px' }}>
                    Could not load analytics: {error.message || "unknown error"}
                </div>
            )}

            <StatGrid>
                <Card className="ih-card">
                    <div style={{ color: 'var(--text-secondary)', fontSize: '13px', marginBottom: '8px' }}>Total Interviews</div>
                    <div style={{ fontSize: '28px', fontWeight: 'bold', color: 'var(--text)' }}>
                        <StatValue loading={isLoading} value={(kpis.total_interviews ?? 0).toLocaleString()} />
                    </div>
                </Card>
                <Card className="ih-card">
                    <div style={{ color: 'var(--text-secondary)', fontSize: '13px', marginBottom: '8px' }}>Completion Rate</div>
                    <div style={{ fontSize: '28px', fontWeight: 'bold', color: 'var(--text)' }}>
                        <StatValue loading={isLoading} value={`${kpis.success_rate ?? 0}%`} />
                    </div>
                </Card>
                <Card className="ih-card">
                    <div style={{ color: 'var(--text-secondary)', fontSize: '13px', marginBottom: '8px' }}>Active Companies</div>
                    <div style={{ fontSize: '28px', fontWeight: 'bold', color: 'var(--text)' }}>
                        <StatValue loading={isLoading} value={(kpis.active_companies ?? 0).toLocaleString()} />
                    </div>
                </Card>
                <Card className="ih-card">
                    <div style={{ color: 'var(--text-secondary)', fontSize: '13px', marginBottom: '8px' }}>Total Candidates</div>
                    <div style={{ fontSize: '28px', fontWeight: 'bold', color: 'var(--text)' }}>
                        <StatValue loading={isLoading} value={(kpis.total_candidates ?? 0).toLocaleString()} />
                    </div>
                </Card>
            </StatGrid>

            <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '20px', marginTop: '20px' }}>
                <SectionCard title="Interview Activity (Last 7 Days)">
                    <div style={{ width: '100%', height: '300px' }}>
                        {!isLoading && interviewsOverTime.length === 0 ? (
                            <div style={{ color: 'var(--text-secondary)', padding: '16px' }}>No interview activity yet.</div>
                        ) : (
                            <ResponsiveContainer>
                                <AreaChart data={interviewsOverTime} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                                    <defs>
                                        <linearGradient id="colorActive" x1="0" y1="0" x2="0" y2="1">
                                            <stop offset="5%" stopColor="var(--primary)" stopOpacity={0.3}/>
                                            <stop offset="95%" stopColor="var(--primary)" stopOpacity={0}/>
                                        </linearGradient>
                                        <linearGradient id="colorCompleted" x1="0" y1="0" x2="0" y2="1">
                                            <stop offset="5%" stopColor="var(--success)" stopOpacity={0.3}/>
                                            <stop offset="95%" stopColor="var(--success)" stopOpacity={0}/>
                                        </linearGradient>
                                    </defs>
                                    <CartesianGrid strokeDasharray="3 3" stroke="var(--border-subtle)" vertical={false} />
                                    <XAxis dataKey="name" stroke="var(--text-muted)" fontSize={12} tickLine={false} axisLine={false} />
                                    <YAxis stroke="var(--text-muted)" fontSize={12} tickLine={false} axisLine={false} />
                                    <Tooltip
                                        contentStyle={{ backgroundColor: 'var(--card)', borderColor: 'var(--border)', borderRadius: '8px', color: 'var(--text)' }}
                                        itemStyle={{ color: 'var(--text)' }}
                                    />
                                    <Area type="monotone" dataKey="active" name="In Progress" stroke="var(--primary)" fillOpacity={1} fill="url(#colorActive)" />
                                    <Area type="monotone" dataKey="completed" name="Completed" stroke="var(--success)" fillOpacity={1} fill="url(#colorCompleted)" />
                                </AreaChart>
                            </ResponsiveContainer>
                        )}
                    </div>
                </SectionCard>

                <SectionCard title="Company Growth (6 Months)">
                    <div style={{ width: '100%', height: '300px' }}>
                        {!isLoading && companyGrowth.length === 0 ? (
                            <div style={{ color: 'var(--text-secondary)', padding: '16px' }}>No company data yet.</div>
                        ) : (
                            <ResponsiveContainer>
                                <BarChart data={companyGrowth} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                                    <CartesianGrid strokeDasharray="3 3" stroke="var(--border-subtle)" vertical={false} />
                                    <XAxis dataKey="name" stroke="var(--text-muted)" fontSize={12} tickLine={false} axisLine={false} />
                                    <YAxis stroke="var(--text-muted)" fontSize={12} tickLine={false} axisLine={false} />
                                    <Tooltip
                                        cursor={{fill: 'var(--surface)'}}
                                        contentStyle={{ backgroundColor: 'var(--card)', borderColor: 'var(--border)', borderRadius: '8px', color: 'var(--text)' }}
                                    />
                                    <Bar dataKey="total" name="Total Companies" fill="var(--primary)" radius={[4, 4, 0, 0]} barSize={24} />
                                </BarChart>
                            </ResponsiveContainer>
                        )}
                    </div>
                </SectionCard>
            </div>
        </DashboardGrid>
    );
}