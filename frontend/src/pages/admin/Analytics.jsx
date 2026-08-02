import {
    LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area
} from "recharts";
import DashboardGrid from "../../layouts/DashboardGrid";
import PageHeader from "../../components/layout/PageHeader";
import StatGrid from "../../components/layout/StatGrid";
import SectionCard from "../../components/layout/SectionCard";
import Card from "../../components/common/Card";

const dailyActivityData = [
    { name: 'Mon', interviews: 400, completions: 240 },
    { name: 'Tue', interviews: 300, completions: 139 },
    { name: 'Wed', interviews: 200, completions: 980 },
    { name: 'Thu', interviews: 278, completions: 390 },
    { name: 'Fri', interviews: 189, completions: 480 },
    { name: 'Sat', interviews: 239, completions: 380 },
    { name: 'Sun', interviews: 349, completions: 430 },
];

const languageUsageData = [
    { name: 'English', value: 75 },
    { name: 'Hindi', value: 20 },
    { name: 'Spanish', value: 5 }
];

export default function Analytics() {
    return (
        <DashboardGrid>
            <PageHeader 
                title="Platform Analytics"
                description="Comprehensive metrics across all companies and candidates."
            />

            <StatGrid>
                <Card className="ih-card">
                    <div style={{ color: 'var(--text-secondary)', fontSize: '13px', marginBottom: '8px' }}>Total Interviews (This Month)</div>
                    <div style={{ fontSize: '28px', fontWeight: 'bold', color: 'var(--text)', display: 'flex', alignItems: 'baseline', gap: '8px' }}>
                        12,450
                        <span style={{ fontSize: '13px', color: 'var(--success)', fontWeight: '500' }}>+14.5%</span>
                    </div>
                </Card>
                <Card className="ih-card">
                    <div style={{ color: 'var(--text-secondary)', fontSize: '13px', marginBottom: '8px' }}>Avg Completion Rate</div>
                    <div style={{ fontSize: '28px', fontWeight: 'bold', color: 'var(--text)', display: 'flex', alignItems: 'baseline', gap: '8px' }}>
                        94.2%
                        <span style={{ fontSize: '13px', color: 'var(--success)', fontWeight: '500' }}>+2.1%</span>
                    </div>
                </Card>
                <Card className="ih-card">
                    <div style={{ color: 'var(--text-secondary)', fontSize: '13px', marginBottom: '8px' }}>Active Companies</div>
                    <div style={{ fontSize: '28px', fontWeight: 'bold', color: 'var(--text)' }}>
                        342
                    </div>
                </Card>
                <Card className="ih-card">
                    <div style={{ color: 'var(--text-secondary)', fontSize: '13px', marginBottom: '8px' }}>Guardrail Interventions</div>
                    <div style={{ fontSize: '28px', fontWeight: 'bold', color: 'var(--danger)', display: 'flex', alignItems: 'baseline', gap: '8px' }}>
                        18
                        <span style={{ fontSize: '13px', color: 'var(--text-secondary)', fontWeight: '500' }}>-5.4%</span>
                    </div>
                </Card>
            </StatGrid>

            <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '20px', marginTop: '20px' }}>
                <SectionCard title="Interview Activity (Weekly)">
                    <div style={{ width: '100%', height: '300px' }}>
                        <ResponsiveContainer>
                            <AreaChart data={dailyActivityData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                                <defs>
                                    <linearGradient id="colorInterviews" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="5%" stopColor="var(--primary)" stopOpacity={0.3}/>
                                        <stop offset="95%" stopColor="var(--primary)" stopOpacity={0}/>
                                    </linearGradient>
                                    <linearGradient id="colorCompletions" x1="0" y1="0" x2="0" y2="1">
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
                                <Area type="monotone" dataKey="interviews" stroke="var(--primary)" fillOpacity={1} fill="url(#colorInterviews)" />
                                <Area type="monotone" dataKey="completions" stroke="var(--success)" fillOpacity={1} fill="url(#colorCompletions)" />
                            </AreaChart>
                        </ResponsiveContainer>
                    </div>
                </SectionCard>

                <SectionCard title="Language Distribution">
                    <div style={{ width: '100%', height: '300px' }}>
                        <ResponsiveContainer>
                            <BarChart data={languageUsageData} layout="vertical" margin={{ top: 10, right: 30, left: 20, bottom: 0 }}>
                                <CartesianGrid strokeDasharray="3 3" stroke="var(--border-subtle)" horizontal={false} />
                                <XAxis type="number" stroke="var(--text-muted)" fontSize={12} tickLine={false} axisLine={false} />
                                <YAxis dataKey="name" type="category" stroke="var(--text-muted)" fontSize={12} tickLine={false} axisLine={false} />
                                <Tooltip 
                                    cursor={{fill: 'var(--surface)'}}
                                    contentStyle={{ backgroundColor: 'var(--card)', borderColor: 'var(--border)', borderRadius: '8px', color: 'var(--text)' }}
                                />
                                <Bar dataKey="value" fill="var(--primary)" radius={[0, 4, 4, 0]} barSize={24} />
                            </BarChart>
                        </ResponsiveContainer>
                    </div>
                </SectionCard>
            </div>
        </DashboardGrid>
    );
}