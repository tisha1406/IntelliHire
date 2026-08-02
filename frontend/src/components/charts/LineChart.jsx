import {
    LineChart as RechartsLineChart, Line, XAxis, YAxis, CartesianGrid,
    Tooltip, ResponsiveContainer, Legend
} from 'recharts';

export default function LineChart({ data, xAxisKey = "name", series = [], height = 300, showLegend = false }) {
    return (
        <div style={{ width: '100%', height }}>
            <ResponsiveContainer>
                <RechartsLineChart data={data} margin={{ top: 10, right: 16, left: 0, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--border)" />
                    <XAxis dataKey={xAxisKey} axisLine={false} tickLine={false}
                        tick={{ fill: 'var(--text-muted)', fontSize: 12 }} dy={10} />
                    <YAxis axisLine={false} tickLine={false}
                        tick={{ fill: 'var(--text-muted)', fontSize: 12 }} dx={-10} />
                    <Tooltip
                        contentStyle={{ backgroundColor: 'var(--surface)', borderColor: 'var(--border)', borderRadius: '8px', color: 'var(--text)' }}
                        itemStyle={{ color: 'var(--text)' }}
                    />
                    {showLegend && <Legend wrapperStyle={{ paddingTop: '16px', fontSize: '13px' }} />}
                    {series.map((s, idx) => (
                        <Line
                            key={idx}
                            type="monotone"
                            dataKey={s.key}
                            stroke={s.color || '#2563EB'}
                            strokeWidth={2}
                            dot={false}
                            activeDot={{ r: 5 }}
                            name={s.label || s.key}
                        />
                    ))}
                </RechartsLineChart>
            </ResponsiveContainer>
        </div>
    );
}
