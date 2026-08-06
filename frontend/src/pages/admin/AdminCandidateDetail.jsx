import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { ArrowLeft, FileText, AlertTriangle } from "lucide-react";
import DashboardGrid from "../../layouts/DashboardGrid";
import PageHeader from "../../components/layout/PageHeader";
import SectionCard from "../../components/layout/SectionCard";
import StatGrid from "../../components/layout/StatGrid";
import ContentGrid from "../../components/layout/ContentGrid";
import Card from "../../components/common/Card";
import Badge from "../../components/common/Badge";
import ActivityTimeline from "../../components/common/ActivityTimeline";
import { MonitoringAPI } from "../../api/monitoring";

export default function AdminCandidateDetail() {
    const { candidateId } = useParams();
    const navigate = useNavigate();
    const [c, setCandidate] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchCandidate = async () => {
            try {
                const data = await MonitoringAPI.getCandidate(candidateId);
                setCandidate(data);
            } catch (err) {
                console.error(err);
            } finally {
                setLoading(false);
            }
        };
        fetchCandidate();
    }, [candidateId]);

    if (loading) return <DashboardGrid><PageHeader title="Loading..." /></DashboardGrid>;
    if (!c) return <DashboardGrid><PageHeader title="Candidate Not Found" /></DashboardGrid>;

    const riskScoreText = c.risk_score || "Low";

    const titleContent = (
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <button onClick={() => navigate("/admin/candidates")}
                style={{ background: 'transparent', border: 'none', color: 'var(--text-secondary)', cursor: 'pointer', display: 'flex', alignItems: 'center' }}>
                <ArrowLeft size={20} />
            </button>
            {c.name}
            <Badge variant={riskScoreText === 'High' ? 'danger' : riskScoreText === 'Medium' ? 'warning' : 'success'}>
                {riskScoreText} Risk
            </Badge>
        </div>
    );

    return (
        <DashboardGrid>
            <PageHeader title={titleContent} description={`${c.company_name || '—'} • ${c.campaign_name || '—'} • ${c.email}`} />

            <StatGrid columns={4}>
                <Card className="ih-card">
                    <div style={{ color: 'var(--text-secondary)', fontSize: '13px', marginBottom: '8px' }}>Readiness Score</div>
                    <div style={{ fontSize: '28px', fontWeight: 'bold', color: 'var(--primary)' }}>{c.readiness_score || 0}%</div>
                </Card>
                <Card className="ih-card">
                    <div style={{ color: 'var(--text-secondary)', fontSize: '13px', marginBottom: '8px' }}>Risk Level</div>
                    <div style={{ fontSize: '24px', fontWeight: 'bold', color: 'var(--success)', height: '38px', display: 'flex', alignItems: 'center' }}>{riskScoreText}</div>
                </Card>
                <Card className="ih-card">
                    <div style={{ color: 'var(--text-secondary)', fontSize: '13px', marginBottom: '8px' }}>Interview Status</div>
                    <div style={{ height: '38px', display: 'flex', alignItems: 'center' }}>
                        <Badge variant="success">{c.status ? c.status.toUpperCase() : '—'}</Badge>
                    </div>
                </Card>
                <Card className="ih-card">
                    <div style={{ color: 'var(--text-secondary)', fontSize: '13px', marginBottom: '8px' }}>Resume Status</div>
                    <div style={{ height: '38px', display: 'flex', alignItems: 'center' }}>
                        <Badge variant="success">{c.resume_status ? c.resume_status.toUpperCase() : '—'}</Badge>
                    </div>
                </Card>
            </StatGrid>

            <ContentGrid>
                <div className="main-content">
                    <SectionCard>
                        <h4 style={{ fontSize: '12px', textTransform: 'uppercase', color: 'var(--text-muted)', marginBottom: '20px', letterSpacing: '0.6px' }}>Interview History</h4>
                        {c.interviews && c.interviews.length > 0 ? c.interviews.map(iv => (
                            <div key={iv.id} style={{ padding: '16px', background: 'var(--surface)', borderRadius: '8px', border: '1px solid var(--border)', marginBottom: '8px' }}>
                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                    <div>
                                        <strong style={{ color: 'var(--text)', display: 'block' }}>{iv.campaign}</strong>
                                        <span style={{ color: 'var(--text-secondary)', fontSize: '13px' }}>{new Date(iv.date).toLocaleDateString()} • {iv.duration}</span>
                                    </div>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                                        <span style={{ fontSize: '22px', fontWeight: 'bold', color: 'var(--primary)' }}>{iv.score}%</span>
                                        <Badge variant="success">{iv.status}</Badge>
                                    </div>
                                </div>
                            </div>
                        )) : (
                            <div style={{ color: 'var(--text-muted)' }}>No interview history found.</div>
                        )}
                    </SectionCard>

                    <SectionCard style={{ marginTop: '16px' }}>
                        <h4 style={{ fontSize: '12px', textTransform: 'uppercase', color: 'var(--text-muted)', marginBottom: '20px', letterSpacing: '0.6px' }}>Profile Details</h4>
                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
                            {[
                                { label: 'Full Name', value: c.name },
                                { label: 'Email', value: c.email },
                                { label: 'Phone', value: c.phone || '—' },
                                { label: 'Company', value: c.company_name || '—' },
                                { label: 'Campaign', value: c.campaign_name || '—' },
                                { label: 'Recruiter', value: c.recruiter_name || '—' },
                            ].map(({ label, value }) => (
                                <div key={label}>
                                    <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: '4px' }}>{label}</div>
                                    <div style={{ color: 'var(--text)', fontWeight: '500' }}>{value}</div>
                                </div>
                            ))}
                        </div>
                    </SectionCard>
                </div>

                <div className="side-content">
                    <SectionCard>
                        <h4 style={{ fontSize: '12px', textTransform: 'uppercase', color: 'var(--text-muted)', marginBottom: '16px', letterSpacing: '0.6px' }}>Activity Timeline</h4>
                        <ActivityTimeline activities={c.activities || []} />
                    </SectionCard>
                </div>
            </ContentGrid>
        </DashboardGrid>
    );
}
