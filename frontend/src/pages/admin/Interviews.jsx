import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Download, Filter } from "lucide-react";
import DashboardGrid from "../../layouts/DashboardGrid";
import PageHeader from "../../components/layout/PageHeader";
import SectionCard from "../../components/layout/SectionCard";
import StatGrid from "../../components/layout/StatGrid";
import Card from "../../components/common/Card";
import DataTable from "../../components/common/DataTable";
import Button from "../../components/common/Button";
import Badge from "../../components/common/Badge";
import { MonitoringAPI } from "../../api/monitoring";

const statusVariant = { completed: 'success', invited: 'warning', abandoned: 'danger', scheduled: 'primary' };

export default function Interviews() {
    const navigate = useNavigate();
    const [statusFilter, setStatusFilter] = useState("all");
    const [interviews, setInterviews] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchInterviews = async () => {
            setLoading(true);
            try {
                const data = await MonitoringAPI.getInterviews({ 
                    limit: 100,
                    status: statusFilter === 'all' ? undefined : statusFilter
                });
                setInterviews(data);
            } catch (err) {
                console.error(err);
            } finally {
                setLoading(false);
            }
        };
        fetchInterviews();
    }, [statusFilter]);

    const columns = [
        {
            title: "Candidate", dataIndex: "candidate_name", sortable: true,
            render: (val, row) => (
                <div>
                    <strong style={{ color: 'var(--text)', display: 'block' }}>{val || 'Unknown Candidate'}</strong>
                    <span style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>{row.id}</span>
                </div>
            )
        },
        { title: "Company", dataIndex: "company_name", sortable: true },
        { title: "Campaign", dataIndex: "campaign_title", sortable: true },
        { title: "Mode", dataIndex: "mode", sortable: true, render: (val) => <span style={{ color: 'var(--text-secondary)' }}>{val?.toUpperCase() || 'N/A'}</span> },
        { title: "Language", dataIndex: "language", sortable: true },
        { title: "AI Model", dataIndex: "ai_model", sortable: true, render: (val) => val ? <code style={{ color: 'var(--primary)', background: 'var(--primary-subtle)', padding: '2px 8px', borderRadius: '4px', fontSize: '12px' }}>{val}</code> : '—' },
        { title: "Duration", dataIndex: "duration", sortable: true, align: "right", render: (val) => val ? `${val}m` : '—' },
        { title: "Score", dataIndex: "score", sortable: true, align: "right", render: (val) => val ? <strong>{val}%</strong> : '—' },
        { title: "Status", dataIndex: "status", sortable: true, render: (val) => <Badge variant={statusVariant[val?.toLowerCase()] || 'primary'}>{val?.toUpperCase()}</Badge> },
    ];

    const rightContent = (
        <Button variant="primary"><Download size={16} /> Export CSV</Button>
    );

    return (
        <DashboardGrid>
            <PageHeader title="Interviews" description="Monitor all AI interview sessions across every company and campaign." rightContent={rightContent} />

            <StatGrid>
                <Card className="ih-card">
                    <div style={{ color: 'var(--text-secondary)', fontSize: '13px', marginBottom: '8px' }}>Total Interviews</div>
                    <div style={{ fontSize: '28px', fontWeight: 'bold', color: 'var(--text)' }}>{interviews.length}</div>
                </Card>
                <Card className="ih-card">
                    <div style={{ color: 'var(--text-secondary)', fontSize: '13px', marginBottom: '8px' }}>Completed</div>
                    <div style={{ fontSize: '28px', fontWeight: 'bold', color: 'var(--success)' }}>{interviews.filter(i => i.status === 'completed').length}</div>
                </Card>
                <Card className="ih-card">
                    <div style={{ color: 'var(--text-secondary)', fontSize: '13px', marginBottom: '8px' }}>Abandoned</div>
                    <div style={{ fontSize: '28px', fontWeight: 'bold', color: 'var(--danger)' }}>{interviews.filter(i => i.status === 'abandoned').length}</div>
                </Card>
                <Card className="ih-card">
                    <div style={{ color: 'var(--text-secondary)', fontSize: '13px', marginBottom: '8px' }}>Pending</div>
                    <div style={{ fontSize: '28px', fontWeight: 'bold', color: 'var(--primary)' }}>{interviews.filter(i => i.status === 'invited' || i.status === 'scheduled').length}</div>
                </Card>
            </StatGrid>

            <SectionCard>
                <div style={{ display: 'flex', gap: '8px', marginBottom: '20px' }}>
                    {["all", "completed", "invited", "abandoned"].map(f => (
                        <button key={f} onClick={() => setStatusFilter(f)} style={{
                            padding: '6px 14px', borderRadius: '20px', border: '1px solid var(--border)',
                            background: statusFilter === f ? 'var(--primary)' : 'transparent',
                            color: statusFilter === f ? 'white' : 'var(--text-secondary)',
                            cursor: 'pointer', fontSize: '13px', fontWeight: '500',
                            transition: 'all 0.15s ease', textTransform: 'capitalize'
                        }}>
                            {f === 'all' ? 'All Interviews' : f}
                        </button>
                    ))}
                </div>
                {loading ? <div style={{ padding: '24px', textAlign: 'center' }}>Loading...</div> : (
                    <DataTable
                        columns={columns}
                        data={interviews}
                        keyField="id"
                        searchable={true}
                    />
                )}
            </SectionCard>
        </DashboardGrid>
    );
}
