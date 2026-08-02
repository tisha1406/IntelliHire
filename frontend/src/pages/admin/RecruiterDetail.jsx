import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { ArrowLeft, Edit, Trash2, ShieldOff, ShieldCheck, KeyRound, Mail } from "lucide-react";
import DashboardGrid from "../../layouts/DashboardGrid";
import PageHeader from "../../components/layout/PageHeader";
import SectionCard from "../../components/layout/SectionCard";
import StatGrid from "../../components/layout/StatGrid";
import ContentGrid from "../../components/layout/ContentGrid";
import Card from "../../components/common/Card";
import Button from "../../components/common/Button";
import Badge from "../../components/common/Badge";
import ActivityTimeline from "../../components/common/ActivityTimeline";
import Modal from "../../components/common/Modal";
import { RecruitersAPI } from "../../api/recruiters";

export default function RecruiterDetail() {
    const { recruiterId } = useParams();
    const navigate = useNavigate();
    const [confirmModal, setConfirmModal] = useState(null);
    const [r, setRecruiter] = useState(null);
    const [loading, setLoading] = useState(true);

    const fetchRecruiter = async () => {
        try {
            const data = await RecruitersAPI.getRecruiter(recruiterId);
            setRecruiter(data);
        } catch (err) {
            console.error("Failed to fetch recruiter:", err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchRecruiter();
    }, [recruiterId]);

    const handleAction = async () => {
        try {
            if (confirmModal === 'delete') {
                await RecruitersAPI.deleteRecruiter(recruiterId);
                navigate("/admin/recruiters");
            } else if (confirmModal === 'suspend') {
                await RecruitersAPI.suspendRecruiter(recruiterId);
                fetchRecruiter();
                setConfirmModal(null);
            } else if (confirmModal === 'activate') {
                await RecruitersAPI.activateRecruiter(recruiterId);
                fetchRecruiter();
                setConfirmModal(null);
            }
        } catch (err) {
            console.error("Action failed:", err);
        }
    };

    if (loading) return <DashboardGrid><PageHeader title="Loading..." /></DashboardGrid>;
    if (!r) return <DashboardGrid><PageHeader title="Recruiter Not Found" /></DashboardGrid>;

    const titleContent = (
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <button onClick={() => navigate("/admin/recruiters")}
                style={{ background: 'transparent', border: 'none', color: 'var(--text-secondary)', cursor: 'pointer', display: 'flex', alignItems: 'center' }}>
                <ArrowLeft size={20} />
            </button>
            {r.name}
            <Badge variant={r.status === 'active' ? 'success' : r.status === 'suspended' ? 'danger' : 'warning'}>{r.status?.toUpperCase()}</Badge>
        </div>
    );

    const rightContent = (
        <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
            {r.status === 'active' ? (
                <Button variant="outline" onClick={() => setConfirmModal('suspend')}><ShieldOff size={15} /> Suspend</Button>
            ) : (
                <Button variant="success" onClick={() => setConfirmModal('activate')}><ShieldCheck size={15} /> Activate</Button>
            )}
            <Button variant="danger" onClick={() => setConfirmModal('delete')}><Trash2 size={15} /> Delete</Button>
        </div>
    );

    return (
        <DashboardGrid>
            <PageHeader title={titleContent} description={`${r.company_name} • ${r.role} • Joined ${new Date(r.created_at).toLocaleDateString()}`} rightContent={rightContent} />

            <StatGrid columns={3}>
                <Card className="ih-card">
                    <div style={{ color: 'var(--text-secondary)', fontSize: '13px', marginBottom: '8px' }}>Interviews Managed</div>
                    <div style={{ fontSize: '28px', fontWeight: 'bold', color: 'var(--text)' }}>0</div>
                </Card>
                <Card className="ih-card">
                    <div style={{ color: 'var(--text-secondary)', fontSize: '13px', marginBottom: '8px' }}>Completions</div>
                    <div style={{ fontSize: '28px', fontWeight: 'bold', color: 'var(--success)' }}>0</div>
                </Card>
                <Card className="ih-card">
                    <div style={{ color: 'var(--text-secondary)', fontSize: '13px', marginBottom: '8px' }}>Avg Candidate Score</div>
                    <div style={{ fontSize: '28px', fontWeight: 'bold', color: 'var(--primary)' }}>0%</div>
                </Card>
            </StatGrid>

            <ContentGrid
                left={
                    <SectionCard>
                        <div style={{ padding: '20px 24px' }}>
                            <h4 style={{ fontSize: '12px', textTransform: 'uppercase', color: 'var(--text-muted)', marginBottom: '20px', letterSpacing: '0.6px' }}>Contact Information</h4>
                            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
                                {[
                                    { label: 'Email', value: r.email },
                                    { label: 'Company', value: r.company_name },
                                    { label: 'Role', value: r.role?.toUpperCase() },
                                    { label: 'Account Status', value: <Badge variant={r.status === 'active' ? 'success' : 'warning'}>{r.status}</Badge> },
                                ].map(({ label, value }) => (
                                    <div key={label}>
                                        <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: '4px' }}>{label}</div>
                                        <div style={{ color: 'var(--text)', fontWeight: '500' }}>{value}</div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </SectionCard>
                }
                right={
                    <SectionCard>
                        <div style={{ padding: '20px 24px' }}>
                            <h4 style={{ fontSize: '12px', textTransform: 'uppercase', color: 'var(--text-muted)', marginBottom: '16px', letterSpacing: '0.6px' }}>Activity Timeline</h4>
                            <ActivityTimeline activities={[]} />
                        </div>
                    </SectionCard>
                }
            />

            <Modal
                isOpen={!!confirmModal}
                onClose={() => setConfirmModal(null)}
                title={confirmModal === 'delete' ? 'Delete Recruiter' : confirmModal === 'suspend' ? 'Suspend Recruiter' : 'Activate Recruiter'}
                footer={
                    <>
                        <Button variant="outline" onClick={() => setConfirmModal(null)}>Cancel</Button>
                        <Button variant={confirmModal === 'delete' || confirmModal === 'suspend' ? 'danger' : 'primary'} onClick={handleAction}>
                            {confirmModal === 'delete' ? 'Delete' : confirmModal === 'suspend' ? 'Suspend' : 'Activate'}
                        </Button>
                    </>
                }
            >
                <p style={{ color: 'var(--text-secondary)', lineHeight: '1.6' }}>
                    {confirmModal === 'delete' && `Are you sure you want to permanently delete ${r.name}? This cannot be undone.`}
                    {confirmModal === 'suspend' && `This will suspend ${r.name}'s access immediately. They will not be able to login until reactivated.`}
                    {confirmModal === 'activate' && `This will activate ${r.name}'s account, allowing them to log in.`}
                </p>
            </Modal>
        </DashboardGrid>
    );
}
