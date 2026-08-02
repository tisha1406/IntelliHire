import { AreaChart, Area, ResponsiveContainer, Tooltip } from 'recharts';

export default function SparkLine({ data, dataKey = "value", color = "var(--primary)", height = 40 }) {
    return (
        <div style={{ width: '100%', height }}>
            <ResponsiveContainer>
                <AreaChart data={data} margin={{ top: 2, right: 2, left: 2, bottom: 2 }}>
                    <defs>
                        <linearGradient id={`spark-${color}`} x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor={color} stopOpacity={0.25} />
                            <stop offset="95%" stopColor={color} stopOpacity={0} />
                        </linearGradient>
                    </defs>
                    <Tooltip
                        contentStyle={{ backgroundColor: 'var(--surface)', borderColor: 'var(--border)', borderRadius: '6px', fontSize: '11px' }}
                        itemStyle={{ color: 'var(--text)' }}
                    />
                    <Area
                        type="monotone" dataKey={dataKey}
                        stroke={color} strokeWidth={1.5}
                        fill={`url(#spark-${color})`}
                        dot={false}
                    />
                </AreaChart>
            </ResponsiveContainer>
        </div>
    );
}
