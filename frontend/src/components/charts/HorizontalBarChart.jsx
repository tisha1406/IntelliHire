import {
    BarChart, Bar, XAxis, YAxis, CartesianGrid,
    Tooltip, ResponsiveContainer, Cell
} from 'recharts';

export default function HorizontalBarChart({ data, nameKey = "name", valueKey = "value", height = 260, color = "var(--primary)" }) {
    return (
        <div style={{ width: '100%', height }}>
            <ResponsiveContainer>
                <BarChart data={data} layout="vertical" margin={{ top: 4, right: 24, left: 8, bottom: 4 }}>
                    <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="var(--border)" />
                    <XAxis type="number" axisLine={false} tickLine={false}
                        tick={{ fill: 'var(--text-muted)', fontSize: 12 }} />
                    <YAxis type="category" dataKey={nameKey} axisLine={false} tickLine={false}
                        tick={{ fill: 'var(--text-secondary)', fontSize: 13 }} width={120} />
                    <Tooltip
                        cursor={{ fill: 'var(--surface)' }}
                        contentStyle={{ backgroundColor: 'var(--surface)', borderColor: 'var(--border)', borderRadius: '8px', color: 'var(--text)' }}
                    />
                    <Bar dataKey={valueKey} radius={[0, 6, 6, 0]} barSize={20}>
                        {data.map((entry, index) => (
                            <Cell key={index} fill={entry.color || color} />
                        ))}
                    </Bar>
                </BarChart>
            </ResponsiveContainer>
        </div>
    );
}
