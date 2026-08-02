import Card from "../../common/Card";
import AreaChart from "../../charts/AreaChart";

export default function MonthlyHiringChart({ data, loading }) {
    if (loading) {
        return (
            <Card title="Hiring Trends" subtitle="Monthly applications vs hires">
                <div style={{ height: '300px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-secondary)' }}>
                    Loading chart data...
                </div>
            </Card>
        );
    }

    return (
        <Card title="Hiring Trends" subtitle="Interviews over time">
            <AreaChart 
                data={data || []} 
                series={[
                    { key: "completed", color: "var(--primary)" },
                    { key: "active", color: "var(--success)" }
                ]}
            />
        </Card>
    );
}
