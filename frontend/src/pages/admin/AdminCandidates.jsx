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

const riskColors = { Low: 'success', Medium: 'warning', High: 'danger' };
const statusColors = { completed: 'success', invited: 'warning', failed: 'danger' };

export default function AdminCandidates() {
    const navigate = useNavigate();
    const [filter, setFilter] = useState("all");
    const [candidates, setCandidates] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchCandidates = async () => {
            setLoading(true);
            try {
                const data = await MonitoringAPI.getCandidates({ 
                    limit: 100,
                    status: filter === 'all' ? undefined : filter
                });
                setCandidates(data);
            } catch (err) {
                console.error(err);
            } finally {
                setLoading(false);
            }
        };
        fetchCandidates();
    }, [filter]);

    const columns = [
        {
            title: "Candidate", dataIndex: "name", sortable: true,
            render: (val, row) => (
                <div style={{ display: 'flex', flexDirection: 'column' }}>
                    <strong style={{ color: 'var(--text)' }}>{val}</strong>
                    <span style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>{row.email}</span>
                </div>
            )
        },
        { title: "Company", dataIndex: "company_name", sortable: true },
        { title: "Resume", dataIndex: "resume_status", sortable: true, render: (val) => <Badge variant={val === 'screened' ? 'success' : 'warning'}>{val?.toUpperCase()}</Badge> },
        {
            title: "Readiness", dataIndex: "readiness_score", sortable: true, align: "right",
            render: (val) => val ? (
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', justifyContent: 'flex-end' }}>
                    <div style={{ width: '60px', height: '6px', background: 'var(--border)', borderRadius: '3px', overflow: 'hidden' }}>
                        <div style={{ width: `${val}%`, height: '100%', background: val >= 75 ? 'var(--success)' : val >= 50 ? 'var(--warning)' : 'var(--danger)', borderRadius: '3px' }} />
                    </div>
                    <span style={{ fontWeight: '600', color: 'var(--text)', minWidth: '32px' }}>{val}%</span>
                </div>
            ) : <span style={{ color: 'var(--text-muted)' }}>—</span>
        },
        { title: "Status", dataIndex: "status", sortable: true, render: (val) => <Badge variant={statusColors[val?.toLowerCase()] || 'primary'}>{val?.toUpperCase()}</Badge> },
        { title: "Joined At", dataIndex: "created_at", sortable: true, align: "right", render: (val) => new Date(val).toLocaleDateString() },
    ];

    const rightContent = (
        <Button variant="outline"><Download size={16} /> Export</Button>
    );

    return (
        <DashboardGrid>
            <PageHeader title="Candidates" description="Platform-wide candidate monitoring. View readiness scores, risk levels, and interview status." rightContent={rightContent} />

            <StatGrid>
                <Card className="ih-card">
                    <div style={{ color: 'var(--text-secondary)', fontSize: '13px', marginBottom: '8px' }}>Total Candidates</div>
                    <div style={{ fontSize: '28px', fontWeight: 'bold', color: 'var(--text)' }}>{candidates.length}</div>
                </Card>
                <Card className="ih-card">
                    <div style={{ color: 'var(--text-secondary)', fontSize: '13px', marginBottom: '8px' }}>Completed Interviews</div>
                    <div style={{ fontSize: '28px', fontWeight: 'bold', color: 'var(--success)' }}>{candidates.filter(c => c.status === 'completed').length}</div>
                </Card>
                <Card className="ih-card">
                    <div style={{ color: 'var(--text-secondary)', fontSize: '13px', marginBottom: '8px' }}>Pending</div>
                    <div style={{ fontSize: '28px', fontWeight: 'bold', color: 'var(--warning)' }}>{candidates.filter(c => c.status === 'invited').length}</div>
                </Card>
            </StatGrid>

            <SectionCard>
                <div style={{ display: 'flex', gap: '8px', marginBottom: '20px' }}>
                    {["all", "completed", "invited", "failed"].map(f => (
                        <button key={f} onClick={() => setFilter(f)} style={{
                            padding: '6px 14px', borderRadius: '20px', border: '1px solid var(--border)',
                            background: filter === f ? 'var(--primary)' : 'transparent',
                            color: filter === f ? 'white' : 'var(--text-secondary)',
                            cursor: 'pointer', fontSize: '13px', fontWeight: '500',
                            transition: 'all 0.15s ease', textTransform: 'capitalize'
                        }}>
                            {f === 'all' ? 'All Candidates' : f}
                        </button>
                    ))}
                </div>
                {loading ? <div style={{ padding: '24px', textAlign: 'center' }}>Loading...</div> : (
                    <DataTable
                        columns={columns}
                        data={candidates}
                        keyField="id"
                        searchable={true}
                        onRowClick={(row) => navigate(`/admin/candidates/${row.id}`)}
                    />
                )}
            </SectionCard>
        </DashboardGrid>
    );
}
