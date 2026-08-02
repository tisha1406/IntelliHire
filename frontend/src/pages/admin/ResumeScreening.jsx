import { useState, useEffect } from "react";
import { Download, RefreshCw } from "lucide-react";
import DashboardGrid from "../../layouts/DashboardGrid";
import PageHeader from "../../components/layout/PageHeader";
import SectionCard from "../../components/layout/SectionCard";
import StatGrid from "../../components/layout/StatGrid";
import Card from "../../components/common/Card";
import DataTable from "../../components/common/DataTable";
import Button from "../../components/common/Button";
import Badge from "../../components/common/Badge";
import { AICenterAPI } from "../../api/ai_center";

const statusVariant = { passed: 'success', screened: 'success', rejected: 'danger', review: 'warning', pending: 'primary' };

export default function ResumeScreening() {
    const [statusFilter, setStatusFilter] = useState("all");
    const [screenings, setScreenings] = useState([]);
    const [loading, setLoading] = useState(true);

    const fetchScreenings = async () => {
        setLoading(true);
        try {
            const data = await AICenterAPI.getResumeScreening({ 
                limit: 100,
                status: statusFilter === 'all' ? undefined : statusFilter
            });
            setScreenings(data);
        } catch (err) {
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchScreenings();
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
        {
            title: "Match Score", dataIndex: "score", sortable: true, align: "right",
            render: (val) => val ? (
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', justifyContent: 'flex-end' }}>
                    <div style={{ width: '60px', height: '6px', background: 'var(--border)', borderRadius: '3px', overflow: 'hidden' }}>
                        <div style={{ width: `${val}%`, height: '100%', background: val >= 80 ? 'var(--success)' : val >= 60 ? 'var(--warning)' : 'var(--danger)' }} />
                    </div>
                    <span style={{ fontWeight: '600', color: 'var(--text)', minWidth: '32px' }}>{val}%</span>
                </div>
            ) : <span style={{ color: 'var(--text-muted)' }}>—</span>
        },
        { title: "Status", dataIndex: "status", sortable: true, render: (val) => <Badge variant={statusVariant[val?.toLowerCase()] || 'primary'}>{val?.toUpperCase()}</Badge> },
        { title: "Processing Time", dataIndex: "processing_time", sortable: true, align: "right", render: (val) => val ? <code style={{ color: 'var(--text-secondary)', fontSize: '12px' }}>{val}</code> : '—' },
        { title: "Date", dataIndex: "created_at", sortable: true, align: "right", render: (val) => new Date(val).toLocaleDateString() },
    ];

    const rightContent = (
        <div style={{ display: 'flex', gap: '12px' }}>
            <Button variant="outline" onClick={fetchScreenings}><RefreshCw size={16} /></Button>
            <Button variant="primary"><Download size={16} /> Export</Button>
        </div>
    );

    return (
        <DashboardGrid>
            <PageHeader title="Resume Screening" description="Monitor AI-powered resume screening across all active campaigns." rightContent={rightContent} />

            <StatGrid>
                <Card className="ih-card">
                    <div style={{ color: 'var(--text-secondary)', fontSize: '13px', marginBottom: '8px' }}>Total Screened</div>
                    <div style={{ fontSize: '28px', fontWeight: 'bold', color: 'var(--text)' }}>{screenings.length}</div>
                </Card>
                <Card className="ih-card">
                    <div style={{ color: 'var(--text-secondary)', fontSize: '13px', marginBottom: '8px' }}>Passed</div>
                    <div style={{ fontSize: '28px', fontWeight: 'bold', color: 'var(--success)' }}>{screenings.filter(s => s.status === 'passed' || s.status === 'screened').length}</div>
                </Card>
                <Card className="ih-card">
                    <div style={{ color: 'var(--text-secondary)', fontSize: '13px', marginBottom: '8px' }}>Needs Review</div>
                    <div style={{ fontSize: '28px', fontWeight: 'bold', color: 'var(--warning)' }}>{screenings.filter(s => s.status === 'review').length}</div>
                </Card>
                <Card className="ih-card">
                    <div style={{ color: 'var(--text-secondary)', fontSize: '13px', marginBottom: '8px' }}>Avg Match Score</div>
                    <div style={{ fontSize: '28px', fontWeight: 'bold', color: 'var(--primary)' }}>
                        {screenings.length > 0 && screenings.filter(s => s.score).length > 0 
                            ? Math.round(screenings.filter(s => s.score).reduce((acc, curr) => acc + curr.score, 0) / screenings.filter(s => s.score).length) 
                            : 0}%
                    </div>
                </Card>
            </StatGrid>

            <SectionCard>
                <div style={{ display: 'flex', gap: '8px', marginBottom: '20px' }}>
                    {["all", "screened", "pending"].map(f => (
                        <button key={f} onClick={() => setStatusFilter(f)} style={{
                            padding: '6px 14px', borderRadius: '20px', border: '1px solid var(--border)',
                            background: statusFilter === f ? 'var(--primary)' : 'transparent',
                            color: statusFilter === f ? 'white' : 'var(--text-secondary)',
                            cursor: 'pointer', fontSize: '13px', fontWeight: '500',
                            transition: 'all 0.15s ease', textTransform: 'capitalize'
                        }}>
                            {f === 'all' ? 'All Screenings' : f}
                        </button>
                    ))}
                </div>
                {loading ? <div style={{ padding: '24px', textAlign: 'center' }}>Loading...</div> : (
                    <DataTable
                        columns={columns}
                        data={screenings}
                        keyField="id"
                        searchable={true}
                    />
                )}
            </SectionCard>
        </DashboardGrid>
    );
}
