import { AreaChart as RechartsAreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

export default function AreaChart({ data, xAxisKey = "name", series = [], height = 300 }) {
    return (
        <div style={{ width: '100%', height }}>
            <ResponsiveContainer>
                <RechartsAreaChart data={data} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                    <defs>
                        {series.map((s, idx) => (
                            <linearGradient key={idx} id={`color-${s.key}`} x1="0" y1="0" x2="0" y2="1">
                                <stop offset="5%" stopColor={s.color || "#2563EB"} stopOpacity={0.3}/>
                                <stop offset="95%" stopColor={s.color || "#2563EB"} stopOpacity={0}/>
                            </linearGradient>
                        ))}
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--border)" />
                    <XAxis dataKey={xAxisKey} axisLine={false} tickLine={false} tick={{ fill: 'var(--text-muted)', fontSize: 12 }} dy={10} />
                    <YAxis axisLine={false} tickLine={false} tick={{ fill: 'var(--text-muted)', fontSize: 12 }} dx={-10} />
                    <Tooltip 
                        contentStyle={{ backgroundColor: 'var(--surface)', borderColor: 'var(--border)', borderRadius: 'var(--radius-sm)', color: 'var(--text)' }}
                        itemStyle={{ color: 'var(--text)' }}
                    />
                    {series.map((s, idx) => (
                        <Area 
                            key={idx} 
                            type="monotone" 
                            dataKey={s.key} 
                            stroke={s.color || "#2563EB"} 
                            fillOpacity={1} 
                            fill={`url(#color-${s.key})`} 
                            strokeWidth={2}
                        />
                    ))}
                </RechartsAreaChart>
            </ResponsiveContainer>
        </div>
    );
}
