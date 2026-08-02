import { RadialBarChart, RadialBar, ResponsiveContainer } from 'recharts';

export default function RadialProgressChart({ value = 0, max = 100, size = 140, color = "var(--primary)", label, sublabel }) {
    const percentage = Math.round((value / max) * 100);
    const data = [{ value: percentage, fill: color }];

    return (
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '8px' }}>
            <div style={{ position: 'relative', width: size, height: size }}>
                <ResponsiveContainer width="100%" height="100%">
                    <RadialBarChart
                        cx="50%" cy="50%"
                        innerRadius="70%" outerRadius="100%"
                        data={data}
                        startAngle={90} endAngle={90 - (360 * percentage / 100)}
                    >
                        <RadialBar
                            background={{ fill: 'var(--border)' }}
                            dataKey="value"
                            cornerRadius={8}
                        />
                    </RadialBarChart>
                </ResponsiveContainer>
                <div style={{
                    position: 'absolute', inset: 0,
                    display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center'
                }}>
                    <span style={{ fontSize: `${size * 0.18}px`, fontWeight: 700, color: 'var(--text)', lineHeight: 1 }}>{percentage}%</span>
                </div>
            </div>
            {label && <span style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text)', textAlign: 'center' }}>{label}</span>}
            {sublabel && <span style={{ fontSize: '12px', color: 'var(--text-muted)', textAlign: 'center' }}>{sublabel}</span>}
        </div>
    );
}
